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

"""Start server of FlexVolume driver"""

from oslo_log import log as logging
import sys

from fuxi_kubernetes.common import config
from fuxi_kubernetes.flex_volume_drivers.server import controller


def main():
    config.init(sys.argv[1:])
    logging.setup(config.CONF, 'fuxi-kubernetes')

    controller.init_volume_drivers()
    controller.start(
        "0.0.0.0",
        config.CONF[config.flexvolume_driver_group.name].driver_server_port,
        debug=config.CONF.debug, threaded=True)
