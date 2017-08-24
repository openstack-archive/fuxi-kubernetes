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

"""Start the service of volume provisioner"""

from oslo_log import log as logging
from oslo_service.service import ProcessLauncher
import sys

from fuxi_kubernetes.common import config
from fuxi_kubernetes.provisioner import service


def main():
    config.init(sys.argv[1:])
    logging.setup(config.CONF, 'fuxi-kubernetes')

    launcher = ProcessLauncher(config.CONF)
    launcher.launch_service(service.Service())
    launcher.wait()
