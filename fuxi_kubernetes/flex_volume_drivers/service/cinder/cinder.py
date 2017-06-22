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

from oslo_log import log as logging
from stevedore import driver as import_driver
from stevedore import extension

from fuxi_kubernetes import exceptions
from fuxi_kubernetes.flex_volume_drivers.service import utils

LOG = logging.getLogger(__name__)


class ServiceCinder(object):
    def __init__(self, host_platform):
        host_cls = import_driver.DriverManager(
            'flex_volume_drivers.service.cinder.hosts',
            host_platform).driver
        self._cinder_client = utils.get_cinder_client()
        self._host = host_cls(self._cinder_client)

    def is_attached(self, volume_id, host_name, **kwargs):
        volume = self._get_volume(volume_id)
        if not volume.attachments:
            return False

        return self._host.is_attached(volume, host_name)

    def attach(self, volume_id, host_name, **kwargs):
        self._host.attach(self._get_volume(volume_id), host_name)

    def _get_volume(self, volume_id):
        try:
            self._cinder_client.volumes.get(volume_id)
        except Exception as ex:
            raise exceptions.GetCinderVolumeExcept(volume_id, str(ex))

    @classmethod
    def is_support_host_platform(cls, host_platform):
        mgr = extension.ExtensionManager(
            namespace='flex_volume_drivers.service.cinder.hosts',
        )
        return host_platform in [e.name for e in mgr]
