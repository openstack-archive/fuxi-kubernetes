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

from stevedore import driver as import_driver
from stevedore import extension

from fuxi_kubernetes import exceptions
from fuxi_kubernetes import utils


class ServerCinder(object):

    def __init__(self, host_platform):
        host_cls = import_driver.DriverManager(
            'flex_volume_drivers.server.cinder.hosts',
            host_platform).driver
        self._cinder_client = utils.get_cinder_client()
        self._host = host_cls(self._cinder_client)

    def is_attached(self, volume_id, host_name):
        volume = self._get_volume(volume_id)
        if not volume.attachments:
            return False

        return self._host.is_attached(host_name, volume)

    def attach(self, volume_id, host_name, pv_or_volume_name):
        return self._host.attach(host_name, self._get_volume(volume_id),
                                 pv_or_volume_name)

    def wait_for_attach(self, device_path):
        return self._host.wait_for_attach(device_path)

    def mount_device(self, device_mount_path, device_path):
        self._host.mount_device(device_mount_path, device_path)

    def detach(self, pv_or_volume_name, host_name):
        self._host.detach(host_name, pv_or_volume_name)

    def wait_for_detach(self, device_path):
        self._host.wait_for_detach(device_path)

    def unmount_device(self, device_mount_path):
        self._host.unmount_device(device_mount_path)

    def mount(self, mount_dir):
        self._host.mount(mount_dir)

    def unmount(self, mount_dir):
        self._host.unmount(mount_dir)

    def _get_volume(self, volume_id):
        try:
            return self._cinder_client.volumes.get(volume_id)
        except Exception as ex:
            raise exceptions.GetCinderVolumeException(volume_id, str(ex))

    @classmethod
    def is_support_host_platform(cls, host_platform):
        mgr = extension.ExtensionManager(
            namespace='flex_volume_drivers.server.cinder.hosts',
        )
        return host_platform in [e.name for e in mgr]
