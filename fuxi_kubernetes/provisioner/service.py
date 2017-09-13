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

from oslo_service import service
import time

from fuxi_kubernetes.provisioner import controller


class Service(service.ServiceBase):
    def __init__(self):
        self._controller = controller.Controller()
        self._is_started = False

    def start(self):
        self._controller.start()
        self._is_started = True

    def stop(self):
        self._controller.stop()
        self._is_started = False

    def wait(self):
        while self._is_started:
            time.sleep(1)

    def reset(self):
        pass
