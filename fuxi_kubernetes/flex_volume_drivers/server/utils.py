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

from cinderclient import client as cinder_client
from kuryr.lib import utils as kuryr_utils

from fuxi_kubernetes.common import config as local_config


def _get_keystone_session(conf_group, **kwargs):
    auth_plugin = kuryr_utils.get_auth_plugin(conf_group)
    session = kuryr_utils.get_keystone_session(conf_group, auth_plugin)
    return session, auth_plugin


def get_cinder_client(*args, **kwargs):
    session, auth_plugin = _get_keystone_session(
        local_config.cinder_group.name)

    return cinder_client.Client(
        session=session, auth=auth_plugin,
        region_name=local_config.CONF[
            local_config.cinder_group.name].region_name,
        version=2)
