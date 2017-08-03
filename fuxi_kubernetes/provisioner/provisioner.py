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
from kubernetes import client
from kubernetes.client.models import v1_persistent_volume_claim
from kubernetes import config
from kubernetes import watch
from oslo_log import log as logging
from oslo_service import service

from fuxi_kubernetes.provisioner.watch_framework import controller
from fuxi_kubernetes.provisioner.watch_framework import reflector

LOG = logging.getLogger(__name__)


class Provisioner(service.ServiceBase):
    def __init__(self):
        self._k8s_client = self._create_k8s_client()
        self._pvc_ctl = self._create_pvc_controller(self._k8s_client)

    def start(self):
        self._pvc_ctl.start()

    def stop(self):
        self._pvc_ctl.stop()

    def wait(self):
        pass

    def reset(self):
        pass

    def _create_pvc_controller(self, k8s_client):
        list_func = k8s_client.list_persistent_volume_claim_for_all_namespaces
        w = watch.Watch()
        watch_func = functools.partial(w.stream, list_func)

        resource_event_handler = controller.ResouceEventHandler(
            self._add_pvc, lambda r: r, self._update_pvc)

        return controller.Controller(
            v1_persistent_volume_claim.V1PersistentVolumeClaim,
            meta_namespace_key, reflector.ListerWatcher(list_func, watch_func),
            10, resource_event_handler)

    def _create_k8s_client(self):
        config.load_kube_config('/var/run/kubernetes/admin.kubeconfig')
        return client.CoreV1Api()

    def _add_pvc(self, obj):
        LOG.warn("add_pvc: %s", str(obj))

    def _update_pvc(self, old_obj, new_obj):
        LOG.warn("update pvc")


def meta_namespace_key(obj):
    """Generate a unique key for obj

    :params obj: instance of kubernetes.client.models.V1ObjectMeta
    """
    meta = obj.metadata
    return meta.namespace + meta.name if meta.namespace else meta.name
