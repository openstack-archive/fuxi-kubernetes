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

import os

from kuryr.lib import config as kuryr_config
from oslo_config import cfg
from oslo_log import log as logging

from fuxi_kubernetes.i18n import _
from fuxi_kubernetes.version import version_info

default_opts = [
    cfg.HostAddressOpt('my_ip',
                       help=_('IP address of this machine.')),
    cfg.IntOpt('fuxi_k8s_port',
               default=7878,
               help=_('Port for fuxi-kubernetes volume driver server.')),
    cfg.StrOpt('host_platform',
               default='baremetal',
               help=_('The environment on which volume driver runs. '
                      'optional values are: baremetal')),
    cfg.StrOpt('rootwrap_config',
               default='/etc/fuxi-kubernetes/rootwrap.conf',
               help=_('Path to the rootwrap configuration file to use for '
                      'running commands as root.')),
]

keystone_group = cfg.OptGroup(
    'keystone',
    title='Keystone Options',
    help=_('Configuration options for OpenStack Keystone'))

legacy_keystone_opts = [
    cfg.StrOpt('region',
               default=os.environ.get('REGION'),
               help=_('The region that this machine belongs to.'),
               deprecated_for_removal=True),
    cfg.StrOpt('auth_url',
               default=os.environ.get('IDENTITY_URL'),
               help=_('The URL for accessing the identity service.'),
               deprecated_for_removal=True),
    cfg.StrOpt('admin_user',
               default=os.environ.get('SERVICE_USER'),
               help=_('The username to auth with the identity service.'),
               deprecated_for_removal=True),
    cfg.StrOpt('admin_tenant_name',
               default=os.environ.get('SERVICE_TENANT_NAME'),
               help=_('The tenant name to auth with the identity service.'),
               deprecated_for_removal=True),
    cfg.StrOpt('admin_password',
               default=os.environ.get('SERVICE_PASSWORD'),
               help=_('The password to auth with the identity service.'),
               deprecated_for_removal=True),
    cfg.StrOpt('admin_token',
               default=os.environ.get('SERVICE_TOKEN'),
               help=_('The admin token.'),
               deprecated_for_removal=True),
    cfg.StrOpt('auth_ca_cert',
               default=os.environ.get('SERVICE_CA_CERT'),
               help=_('The CA certification file.'),
               deprecated_for_removal=True),
    cfg.BoolOpt('auth_insecure',
                default=True,
                help=_("Turn off verification of the certificate for ssl."),
                deprecated_for_removal=True),
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

CONF = cfg.CONF
logging.register_options(CONF)
CONF.register_opts(default_opts)
CONF.register_opts(legacy_keystone_opts, group=keystone_group.name)
CONF.register_opts(cinder_opts, group=cinder_group.name)
kuryr_config.register_keystoneauth_opts(CONF, cinder_group.name)
CONF.set_default('auth_type', 'password', cinder_group.name)


def init(args, **kwargs):
    cfg.CONF(args=args, project='fuxi-kubernetes',
             version=version_info.release_string(), **kwargs)
