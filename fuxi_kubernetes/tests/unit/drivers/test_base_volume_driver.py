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
from fuxi_kubernetes.flex_volume_drivers.drivers import base as base_driver
from fuxi_kubernetes.tests.unit import base


class TestBaseVolumeDriver(base.TestCase):

    def setUp(self):
        super(TestBaseVolumeDriver, self).setUp()
        self._driver = base_driver.BaseVolumeDriver()

    def test_empty_argument(self):
        self.assertEqual(constants.RESULT_NOT_SUPPORT,
                         self._driver([]).status)

    def test_invalid_cmd(self):
        self.assertEqual(constants.RESULT_NOT_SUPPORT,
                         self._driver(['abc']).status)

    def test_load_json_fail(self):
        r = self._driver(['attach', 'abc', 'abc'])
        self.assertEqual(constants.RESULT_FAILURE, r.status)
        self.assertIn('can not load json argument', r.message)
