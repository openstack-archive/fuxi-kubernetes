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
from fuxi_kubernetes.flex_volume_drivers.drivers.cinder import client


class DriverCinder(base.BaseVolumeDriver):

    def get_volume_name(self, **kwargs):
        name = kwargs.get(constants.CINDER_VOLUME_ATTR_VOLUME_ID)
        result = self._get_result(name)
        if name:
            result.volumeName = name
        else:
            result.message = 'Can not get volume name'
        return result

    def is_attached(self, host_name, **kwargs):
        ret, info = self._get_driver_client().is_attached(
            host_name, kwargs.get(constants.CINDER_VOLUME_ATTR_VOLUME_ID)
        )
        return self._get_result(ret, info)

    def attach(self, host_name, **kwargs):
        ret, info = self._get_driver_client().attach(
            host_name, kwargs.get(constants.CINDER_VOLUME_ATTR_VOLUME_ID)
        )
        return self._get_result(ret, info)

    def _get_result(self, success=True, info={}):
        info['status'] = constants.STATUS_SUCCESS if success else (
            constants.STATUS_FAILURE)
        return base.Result(**info)

    def _get_driver_client(self):
        return client.VolumeDriverClient(
            constants.VOLUME_DRIVER_CINDER,
            'http://%s:%d' % (self._driver_service_ip,
                              self._driver_service_port))
