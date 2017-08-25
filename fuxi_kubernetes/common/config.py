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

from kuryr.lib import config as kuryr_config
import os
from oslo_config import cfg
from oslo_log import log as logging

from fuxi_kubernetes.common import constants
from fuxi_kubernetes.i18n import _
from fuxi_kubernetes.version import version_info


flexvolume_driver_group = cfg.OptGroup(
    'flexvolume_driver',
    title='FlexVolume driver Options',
    help=_('Configuration options for FlexVolume driver'))

flexvolume_driver_opts = [
    cfg.HostnameOpt('hostname',
                    help=_('Hostname of machine '
                           'on which FlexVolume driver runs.')),
    cfg.HostAddressOpt('node_ip',
                       help=_('IP address of machine '
                              'on which FlexVolume driver runs.')),
    cfg.IntOpt('driver_server_port',
               default=7878,
               help=_('Port for the server of FlexVolume driver.')),
    cfg.StrOpt('host_platform',
               default='baremetal',
               help=_('The platform on which FlexVolume driver runs. '
                      'Optional values are: baremetal')),
    cfg.StrOpt('rootwrap_config',
               default='/etc/fuxi-kubernetes/rootwrap.conf',
               help=_('Path to the rootwrap configuration file to use for '
                      'running commands as root.')),
]


cinder_group = cfg.OptGroup(
    'cinder',
    title='Cinder Options',
    help=_('Configuration options for OpenStack Cinder'))


cinder_opts = [
    cfg.StrOpt('region_name',
               default=os.environ.get('REGION'),
               help=_('Region name of this node. This is used when picking'
                      ' the URL in the service catalog.')),
]


kubernetes_group = cfg.OptGroup(
    'kubernetes',
    title='Kubernetes Options',
    help=_('Configuration options for Kubernetes'))


k8s_opts = [
    cfg.StrOpt('api_root',
               help=_("The root URL of the Kubernetes API"),
               default=os.environ.get('K8S_API', 'http://localhost:8080')),
    cfg.StrOpt('ssl_client_crt_file',
               help=_("Absolute path to client cert to "
                      "connect to HTTPS K8S_API")),
    cfg.StrOpt('ssl_client_key_file',
               help=_("Absolute path client key file to "
                      "connect to HTTPS K8S_API")),
    cfg.StrOpt('ssl_ca_crt_file',
               help=_("Absolute path to ca cert file to "
                      "connect to HTTPS K8S_API")),
    cfg.BoolOpt('ssl_verify_server_crt',
                help=_("HTTPS K8S_API server identity verification"),
                default=False),
    cfg.StrOpt('token_file',
               help=_("The token to talk to the k8s API"),
               default=''),
]


CONF = cfg.CONF
logging.register_options(CONF)
CONF.register_opts(flexvolume_driver_opts, flexvolume_driver_group.name)
CONF.register_opts(k8s_opts, kubernetes_group.name)
CONF.register_opts(cinder_opts, group=cinder_group.name)
kuryr_config.register_keystoneauth_opts(CONF, cinder_group.name)


def init(args, **kwargs):
    cfg.CONF(args=args, project=constants.PROJECT_NAME,
             version=version_info.release_string(), **kwargs)
