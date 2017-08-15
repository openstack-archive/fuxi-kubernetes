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

from stevedore import extension

from fuxi_kubernetes.provisioner import provisioner_deleter as pd
from fuxi_kubernetes import utils


class Controller(object):
    """Controller provisions pv for pvc and deletes released pv"""

    def __init__(self):
        volume_plugins = self._load_volume_plugins()
        k8s_client = utils.get_k8s_client()

        self._provisioner = pd.Provisioner(k8s_client, volume_plugins)
        self._deleter = pd.Deleter(
            self._provisioner, k8s_client, volume_plugins)

    def start(self):
        self._provisioner.start()
        self._deleter.start()

    def stop(self):
        self._provisioner.stop()
        self._deleter.stop()

    def _load_volume_plugins(self):
        mgr = extension.ExtensionManager(
            namespace='volume_provisioner.plugins',
            invoke_on_load=True)
        return {e.name: e.obj for e in mgr}
