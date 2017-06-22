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

from oslo_config import cfg

from fuxi_kubernetes.i18n import _


default_opts = [
    cfg.HostAddressOpt('my_ip',
                       help=_('IP address of this machine.')),
    cfg.IntOpt('server_port',
               default=7878,
               help=_('Port for the server of FlexVolume driver.')),
]


CONF = cfg.CONF
CONF.register_opts(default_opts)
