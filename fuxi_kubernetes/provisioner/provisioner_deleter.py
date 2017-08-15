# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import eventlet
import functools
from kubernetes import client as k8s_client
from kubernetes.client import models as k8s_models
from kubernetes import watch
from oslo_log import log as logging

from fuxi_kubernetes.common import config
from fuxi_kubernetes.common import constants
from fuxi_kubernetes.provisioner.volume_plugins import base_volume_plugin
from fuxi_kubernetes.provisioner.watch_framework import consumer
from fuxi_kubernetes.provisioner.watch_framework import controller
from fuxi_kubernetes.provisioner.watch_framework import producer

LOG = logging.getLogger(__name__)


def _meta_namespace_key(obj):
    """Generate a unique key for obj

    :params obj: instance of kubernetes.client.models.V1ObjectMeta
    """
    meta = obj.metadata
    return meta.namespace + meta.name if meta.namespace else meta.name


def _check_param_type(log_prefix, param_type):

    def decorator_func(f):

        @functools.wraps(f)
        def wrapper(*args):
            for i, p in enumerate(args[1:]):
                if not isinstance(p, param_type):
                    LOG.error("%s, parameter %d of %s is not an instance of ",
                              "%s", log_prefix, i + 2, f.__name__,
                              str(param_type))
                    return
            f(*args)
        return wrapper

    return decorator_func


class _StorageClassWatcher(object):
    def __init__(self):
        self._client = k8s_client.StorageV1beta1Api()
        self._storage_classes = dict()
        self._sc_ctl = None

        self._init_sc_ctl()

    def start(self):
        self._sc_ctl.start()

    def stop(self):
        self._sc_ctl.stop()

    def __getitem__(self, sc_name):
        return self._storage_classes.get(sc_name, None)

    def _init_sc_ctl(self):
        lister_watcher = producer.ListerWatcher(
            self._client.list_storage_class,
            functools.partial(watch.Watch().stream,
                              self._client.list_storage_class)
        )
        self._sc_ctl = controller.Controller(
            k8s_models.V1beta1StorageClass,
            _meta_namespace_key, lister_watcher,
            config.CONF[config.provisioner_group.name].watch_timeout,
            consumer.ResouceEventHandler(
                on_add=self._add_sc, on_delete=self._delete_sc,
                on_update=self._update_sc
            )
        )

    @_check_param_type("Add storage class", k8s_models.V1beta1StorageClass)
    def _add_sc(self, sc):
        self._storage_classes[sc.metadata.name] = sc

    @_check_param_type("Delete storage class", k8s_models.V1beta1StorageClass)
    def _delete_sc(self, sc):
        self._storage_classes.pop(sc.metadata.name, None)

    @_check_param_type("Update storage class", k8s_models.V1beta1StorageClass)
    def _update_sc(self, old_sc, new_sc):
        self._add_sc(new_sc)


class Provisioner(object):
    def __init__(self, k8s_client_instance, provisioner_plugins):
        self._provisioner_plugins = provisioner_plugins
        self._client = k8s_client_instance
        self._sc_watcher = _StorageClassWatcher()
        self._pvc_ctl = None
        self._created_pvs = set()

        self._init_ctl()

    def start(self):
        self._sc_watcher.start()
        self._pvc_ctl.start()

    def stop(self):
        self._sc_watcher.stop()
        self._pvc_ctl.stop()

    def delete_pv(self, pv):
        self._created_pvs.discard(pv.metadata.name)

    def _init_ctl(self):
        lister_watcher = producer.ListerWatcher(
            self._client.list_persistent_volume_claim_for_all_namespaces,
            functools.partial(
                watch.Watch().stream,
                self._client.list_persistent_volume_claim_for_all_namespaces)
        )
        self._pvc_ctl = controller.Controller(
            k8s_models.V1PersistentVolumeClaim,
            _meta_namespace_key, lister_watcher,
            config.CONF[config.provisioner_group.name].watch_timeout,
            consumer.ResouceEventHandler(
                on_add=self._add_pvc, on_delete=lambda r: r,
                on_update=self._update_pvc
            )
        )

    @_check_param_type("Add pvc", k8s_models.V1PersistentVolumeClaim)
    def _add_pvc(self, pvc):
        try:
            self._pre_provision_pv(pvc)
        except Exception as ex:
            LOG.error("Add pvc, can not provision pv, reason: %s", str(ex))
            return

        pv = self._provision_pv(pvc)
        if pv:
            self._created_pvs.add(pv.metadata.name)

    @_check_param_type("Update pvc", k8s_models.V1PersistentVolumeClaim)
    def _update_pvc(self, old_pvc, new_pvc):
        self._add_pvc(new_pvc)

    def _provision_pv(self, pvc):
        # generate claim ref
        claim_ref = self._get_claim_ref(pvc)

        # create storage asset
        sc_name = self._get_pvc_storage_class(pvc)
        sc = self._sc_watcher[sc_name]
        provisioner_plugin = self._provisioner_plugins.get(sc.provisioner)
        pv = None
        try:
            pv = provisioner_plugin.provision(
                base_volume_plugin.VolumeOption(
                    pv_reclaim_policy=constants.K8S_PV_RECLAIM_POLICY_DELETE,
                    pv_name=self._get_pv_name(pvc), pvc=pvc,
                    parameters=sc.parameters)
            )
        except Exception as ex:
            LOG.error("Provision pv, create storage asset failed, reason: %s",
                      str(ex))
            return
        pv.spec.storage_class_name = sc_name
        pv.spec.claim_ref = claim_ref
        pv.metadata.annotations[
            constants.ANNOTATION_DINAMICALLY_PROVISIONED] = sc.provisioner

        retry_count = config.CONF[
            config.provisioner_group.name].create_pv_retry_count
        retry_interval = config.CONF[
            config.provisioner_group.name].create_pv_retry_interval

        # create pv
        for i in range(retry_count):
            try:
                self._client.create_persistent_volume(pv)
                return pv
            except Exception as ex:
                LOG.error("Provision pv, create pv failed, reason: %s",
                          str(ex))

            if i + 1 < retry_count:
                eventlet.sleep(retry_interval)

        # delete storage asset if create pv failed
        LOG.error("Provision pv, create pv failed, reason: exceeds max "
                  "retry times. Start deleting the storage asset")
        for i in range(retry_count):
            try:
                provisioner_plugin.delete(pv)
                return
            except Exception as ex:
                LOG.error("Provision pv, delete storage asset failed, "
                          "reason: %s", str(ex))

            if i + 1 < retry_count:
                eventlet.sleep(retry_interval)

        LOG.error("Provision pv, delete storage asset failed, "
                  "reason: exceeds max retry times")

    def _pre_provision_pv(self, pvc):
        if pvc.spec.volume_name:
            raise Exception("pvc is already bounded")

        if self._get_pv_name(pvc) in self._created_pvs:
            raise Exception('the corresponding pv is already exist')

        provisioner_plugin_name = pvc.metadata.annotations.get(
            constants.ANNOTATION_STORAGE_PROVISIONER)
        if provisioner_plugin_name and (
                provisioner_plugin_name not in self._provisioner_plugins):
            raise Exception("not supported provisioner plugin: %s" % str(
                provisioner_plugin_name))

        sc = self._sc_watcher[self._get_pvc_storage_class(pvc)]
        if not sc:
            raise Exception("does not find coresponding storage class")
        elif sc.provisioner not in self._provisioner_plugins:
            raise Exception("not supported provisioner plugin: %s" % str(
                sc.provisioner))

    def _get_pv_name(self, pvc):
        return "pvc-" + pvc.metadata.uid

    def _get_pvc_storage_class(self, pvc):
        sc_name = pvc.metadata.annotations.get(
            constants.ANNOTATION_BETA_STORAGE_CLASS)
        if sc_name:
            return sc_name

        sc_name = pvc.spec.storage_class_name
        return sc_name if sc_name else ""

    def _get_claim_ref(self, pvc):
        return k8s_models.V1ObjectReference(
            api_version=pvc.api_version,
            kind=pvc.kind,
            name=pvc.metadata.name,
            namespace=pvc.metadata.namespace,
            uid=pvc.metadata.uid,
            resource_version=pvc.metadata.resource_version
        )


class Deleter(object):
    def __init__(self, provisioner, k8s_client_instance, provisioner_plugins):
        self._provisioner_plugins = provisioner_plugins
        self._client = k8s_client_instance
        self._provisioner = provisioner
        self._pv_ctl = None
        self._init_ctl()

    def start(self):
        self._pv_ctl.start()

    def stop(self):
        self._pv_ctl.stop()

    def _init_ctl(self):
        lister_watcher = producer.ListerWatcher(
            self._client.list_persistent_volume,
            functools.partial(watch.Watch().stream,
                              self._client.list_persistent_volume)
        )
        self._pv_ctl = controller.Controller(
            k8s_models.V1PersistentVolume,
            _meta_namespace_key, lister_watcher,
            config.CONF[config.provisioner_group.name].watch_timeout,
            consumer.ResouceEventHandler(
                on_add=lambda r: r, on_delete=lambda r: r,
                on_update=self._update_pv
            )
        )

    @_check_param_type("Update pv", k8s_models.V1PersistentVolume)
    def _update_pv(self, old_pv, new_pv):
        try:
            self._pre_delete_pv(new_pv)
        except Exception as ex:
            LOG.error("Update pv, can not delete pv, reason: %s", str(ex))
            return

        self._provisioner.delete_pv(new_pv)

        self._delete_pv(new_pv)

    def _pre_delete_pv(self, pv):
        if pv.status.phase != constants.K8S_PV_PHASE_RELEASED:
            raise Exception("the status of pv is not Released")

        if pv.spec.persistent_volume_reclaim_policy != (
                constants.K8S_PV_RECLAIM_POLICY_DELETE):
            raise Exception("the reclaim policy of pv is not Delete")

        plugin_name = pv.metadata.annotations.get(
            constants.ANNOTATION_DINAMICALLY_PROVISIONED)
        if plugin_name not in self._provisioner_plugins:
            raise Exception("pv is not created by us")

    def _delete_pv(self, pv):
        plugin = self._provisioner_plugins.get(
            pv.metadata.annotations.get(
                constants.ANNOTATION_DINAMICALLY_PROVISIONED)
        )
        try:
            plugin.delete(pv)
        except Exception as ex:
            LOG.error("Delete the storage asset of pv failed, reason: %s",
                      str(ex))
            return

        try:
            self._client.delete_persistent_volume(
                pv.metdata.name, k8s_models.V1DeleteOptions())
        except Exception as ex:
            LOG.error("Delete pv failed, reason: %s", str(ex))
