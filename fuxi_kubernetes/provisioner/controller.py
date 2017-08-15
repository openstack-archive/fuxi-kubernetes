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

import functools
from kubernetes import client as k8s_client
from kubernetes.client import models as k8s_models
from kubernetes import watch
from oslo_log import log as logging

from fuxi_kubernetes.common import config
from fuxi_kubernetes.common import constants
from fuxi_kubernetes.provisioner.watch_framework import consumer
from fuxi_kubernetes.provisioner.watch_framework import controller
from fuxi_kubernetes.provisioner.watch_framework import producer

LOG = logging.getLogger(__name__)


class _StorageClassWatcher(object):
    def __init__(self):
        self._client = k8s_client.StorageV1beta1Api()
        self._sc_ctl = None
        self._storage_classes = dict()

        self._init_sc_ctl()

    def start(self):
        self._sc_ctl.start()

    def stop(self):
        self._sc_ctl.stop()

    def __getitem__(self. sc_name):
        if sc_name in self._storage_classes:
            return self._storage_classes[sc_name]

        try:
            sc_list = self._client.list_storage_class(
                field_selector='metadata.name=' % sc_name)
            return sc_list[0] if sc_list and len(sc_list) == 1 else None
        except Exception as ex:
            LOG.error("Get storage class: (%s) failed, reason: %s",
                      sc_name, str(ex))
            return None

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
    def __init__(self, provisioner_plugins):
        self._provisioner_plugins = provisioner_plugins
        self._client = client.CoreV1Api()
        self._sc_watcher = _StorageClassWatcher()
        self._pvc_ctl = None

        self._init_ctl()

    def start(self):
        self._sc_watcher.start()
        self._pvc_ctl.start()

    def stop(self):
        self._sc_watcher.stop()
        self._pvc_ctl.stop()

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
        can_provision, msg = self._should_provision_pv(pvc)
        if not can_provision:
            LOG.error("Add pvc, can not provision pv, reason: %s", msg)

        self._provision_pvc(pvc)

    @_check_param_type("Update pvc", k8s_models.V1PersistentVolumeClaim)
    def _update_pvc(self, old_pvc, new_pvc):
        LOG.warn("update pvc, old_pvc=%s, new_pvc=%s", str(old_pvc), str(new_pvc))

    def _provision_pv(self, pvc):
        # check wether pv is exist
        pv_name = "pvc-" + pvc.metadata.uid
        try:
            pvs = self._client.list_persistent_volume(
                field_selector='metadata.name=' % pv_name)
            if pvs:
                LOG.warn("Provision pv, the corresponding pv is already exist")
                return
        except Exception as ex:
            LOG.error("Provision pv, get pv failed, reason: %s", str(ex))
            return

        # generate claim ref
        claim_ref = self._get_claim_ref(pvc)

        # create storage asset
        sc_name = self._get_pvc_storage_class(pvc)
        sc = self._sc_watcher[sc_name]
        if not sc:
            LOG.error("Provision pv, can not find storage class")
            return
        provisioner_plugin = self._provisioner_plugin.get(sc.provisioner)
        pv = None
        try:
            pv = provisioner_plugin.provision(
                provisioner_plugin.VolumeOptions(
                    pv_reclaim_policy=constants.K8S_PV_RECLAIM_POLICY_DELETE,
                    pv_name=pv_name, pvc=pvc, parameters=sc.parameters)
            )
        except Exception as ex:
            LOG.error("Provision pv, create storage asset failed, reason: %s",
                      str(ex))
            return
        pv.spec.claim_ref = claim_ref
        pv.metadata.annotations[
            constants.ANNOTATION_DINAMICALLY_PROVISIONED] = sc.provisioner
        pv.spec.storage_class_name = sc_name

        # create pv
        retry_count = config.CONF[
            config.provisioner_group.name].create_pv_retry_count
        retry_interval = config.CONF[
            config.provisioner_group.name].create_pv_retry_interval
        for i in range(retry_count):
            try:
                self._client.create_persistent_volume(pv)
                return
            except Exception as ex:
                LOG.error("Provision pv, create pv failed, reason: %s", str(ex))
            eventlet.sleep(retry_interval)

        # delete storage asset if create pv failed
        LOG.error("Provision pv, create pv failed, reason: exceeds max "
                  "retry times. Start deleting the storage asset")
        for i in range(retry_count):
            try:
                provisioner_plugin.delete(pv)
                return
            except Exception as ex:
                LOG.error("Provision pv, delete storage asset failed "
                          "after creating pv failed, reason: %s", str(ex))
            eventlet.sleep(retry_interval)

        LOG.error("Provision pv, delete storage asset failed after "
                  "creating pv failed, reason: exceeds max retry times")

    def _should_provision_pv(self, pvc):
        if pvc.spec.volume_name:
            return False, "pvc is already bounded" 

        provisioner_plugin_name = pvc.metadata.annotations.get(
            constants.ANNOTATION_STORAGE_PROVISIONER)
        if provisioner_plugin_name:
            if provisioner_plugin_name in self._provisioner_plugins):
                return True, provisioner_plugin_name
            else:
                return False, "not supported provisioner plugin: %s" % str(
                    provisioner_plugin_name)

        sc = self._sc_watcher[self._get_pvc_storage_class(pvc)]
        if sc:
            if sc.provisioner in self._provisioner_plugins):
                return True, sc.provisioner
            else:
                return False, "not supported provisioner plugin: %s" % str(
                    sc.provisioner)
        return False, "not find provisioner"

    def _get_pvc_storage_class(self, pvc):
        sc_name = pvc.metadata.annotations.get(
            constants.ANNOTATION_BETA_STORAGE_CLASS)
        if sc_name:
            return sc_name

        sc_name = pvc.spec.storage_class_name
        return sc_name if sc_name else ""

    def _get_claim_ref(self. pvc):
        return k8s_models.V1ObjectReference(
            api_version=pvc.api_version,
            kind=pvc.kind,
            name=pvc.metadata.name,
            namespace=pvc.metadata.namespace,
            uid=pvc.metadata.uid,
            resource_version=pvc.metadata.resource_version
        )


class Deleter(object):
    def __init__(self, provisioner_plugins):
        self._provisioner_plugins = provisioner_plugins
        self._client = client.CoreV1Api()
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
        self._pvc_ctl = controller.Controller(
            k8s_models.V1PersistentVolume,
            _meta_namespace_key, lister_watcher,
            config.CONF[config.provisioner_group.name].watch_timeout,
            consumer.ResouceEventHandler(
                on_add=lambda r: r, on_delete=lambda r: r,
                on_update=self._update_pv
            )
        )

    @_check_param_type("Update pv", k8s_models.V1PersistentVolume)
    def self._update_pv(self. old_pv, new_pv):
        can_delete, msg = self._should_delete_pv(pv)
        if not can_delete:
            LOG.error("Update pv, can not delete pv, reason: %s", msg)
            return

        self._delete_pv(pv)

    def _should_delete_pv(self. pv):
        if pv.status.phase != constants.K8S_PV_PHASE_RELEASED:
            return False, "the status of pv is not Released"

        if pv.spec.persistent_volume_reclaim_policy != (
                constants.K8S_PV_RECLAIM_POLICY_DELETE):
            return False, "the reclaim policy of pv is not Delete"

        plugin_name = pv.metadata.annotations.get(
            constants.ANNOTATION_DINAMICALLY_PROVISIONED)
        if plugin_name not in self._provisioner_plugins:
            return False "pv is not created by us"

        return True, None

    def _delete_pv(self, pv):
        plugin = self._provisioner_plugins.get(
            pv.metadata.annotations.get(
                constants.ANNOTATION_DINAMICALLY_PROVISIONED)
        )
        try:
            plugin.delete(pv):
        except Exception as ex:
            LOG.error("Delete the storage asset of pv failed, reason: %s",
                      str(ex))
            return

        try:
            self._client.delete_persistent_volume(
                pv.metdata.name, k8s_models.V1DeleteOptions())
        except Exception as ex:
            LOG.error("Delete pv failed, reason: %s", str(ex))


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
                    LOG.error("%s, parameter %d of %s is not an instance of %s",
                              log_prefix, i + 2, f.__name__, str(param_type))
                    return
            f(*args)
        return wrapper

    return decorator_func 
