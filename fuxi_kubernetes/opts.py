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

__all__ = [
    'list_fuxi_k8s_opts',
]

import itertools
from kuryr.lib import opts as kuryr_opts
from oslo_log import _options

from fuxi_kubernetes.common import config


def list_fuxi_k8s_opts():
    auth_opts = kuryr_opts.get_keystoneauth_conf_options()

    return [
        ('DEFAULT',
         itertools.chain(config.default_opts, _options.list_opts()[0][1])),

        (config.cinder_group.name,
         itertools.chain(config.cinder_opts, auth_opts,)),
    ]
