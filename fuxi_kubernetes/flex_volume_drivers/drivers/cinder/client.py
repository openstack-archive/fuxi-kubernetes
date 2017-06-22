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
import requests

from fuxi_kubernetes.common import constants

LOG = logging.getLogger(__name__)


class VolumeDriverClient(object):
    def __init__(self, driver_name, endpoint):
        self._driver = driver_name
        self._endpoint = endpoint

    def is_attached(self, host_name, volume_id):
        return self._send_and_receive(
            constants.SERCIE_API_IS_ATTACHED,
            {'host_name': host_name,
             'volume_id': volume_id}
        )

    def attach(self, host_name, volume_id):
        return self._send_and_receive(
            constants.SERCIE_API_ATTACH,
            {'host_name': host_name,
             'volume_id': volume_id}
        )

    def _send_and_receive(self, api, data):
        try:
            data['driver'] = self._driver
            response = requests.post(self._endpoint + api, json=data)
            if not response.ok:
                return False, {'message': response.text}

            return True, response.json()

        except Exception as ex:
            return False, {'message': 'Some exception:(%s) happens' % str(ex)}
