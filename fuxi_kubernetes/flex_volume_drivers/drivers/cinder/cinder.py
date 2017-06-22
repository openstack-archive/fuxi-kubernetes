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

from fuxi_kubernetes.common import constants
from fuxi_kubernetes.flex_volume_drivers.drivers import base


class DriverCinder(base.BaseVolumeDriver):

    def __init__(self):
        super(DriverCinder, self).__init__()
        self._driver_name = constants.VOLUME_DRIVER_CINDER

    def get_volume_name(self, **kwargs):
        name = self._volumeid(kwargs)
        if name:
            return self._generate_result(True, {'volumeName': name})
        return self._generate_result(
            False, {'message': 'Can not get volume name'})

    def is_attached(self, host_name, **kwargs):
        return self._request_server(
            constants.SERVER_API_IS_ATTACHED,
            {'host_name': host_name,
             'volume_id': self._volumeid(kwargs)}
        )

    def attach(self, host_name, **kwargs):
        return self._request_server(
            constants.SERVER_API_ATTACH,
            {'host_name': host_name,
             'volume_id': self._volumeid(kwargs)}
        )

    def wait_for_attach(self, device_path, **kwargs):
        params = {'device_path': device_path}
        params.update(kwargs)
        return self._request_server(
            constants.SERVER_API_WAIT_FOR_ATTACH,
            params
        )

    def mount_device(self, device_mount_path, device_path, **kwargs):
        params = {
            'device_mount_path': device_mount_path,
            'device_path': device_path
        }
        params.update(kwargs)
        return self._request_server(
            constants.SERVER_API_MOUNT_DEVICE,
            params
        )

    def detach(self, device_path, host_name):
        return self._request_server(
            constants.SERVER_API_DETACH,
            {'device_path': device_path, 'host_name': host_name}
        )

    def wait_for_detach(self, device_path):
        return self._request_server(
            constants.SERVER_API_WAIT_FOR_DETACH,
            {'device_path': device_path}
        )

    def unmount_device(self, device_mount_path):
        return self._request_server(
            constants.SERVER_API_UNMOUNT_DEVICE,
            {'device_mount_path': device_mount_path}
        )

    def mount(self, mount_dir, **kwargs):
        params = {'mount_dir': mount_dir}
        params.update(kwargs)
        return self._request_server(
            constants.SERVER_API_MOUNT,
            params
        )

    def unmount(self, mount_dir):
        return self._request_server(
            constants.SERVER_API_UNMOUNT,
            {'mount_dir': mount_dir}
        )

    def _volumeid(self, params):
        return params.get(constants.CINDER_VOLUME_ATTR_VOLUME_ID)
