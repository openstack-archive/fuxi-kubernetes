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
from kubernetes import client as k8s_client
from kuryr.lib import utils as kuryr_utils
import os

from fuxi_kubernetes.common import config


def _get_keystone_session(conf_group, **kwargs):
    auth_plugin = kuryr_utils.get_auth_plugin(conf_group)
    session = kuryr_utils.get_keystone_session(conf_group, auth_plugin)
    return session, auth_plugin


def get_cinder_client(*args, **kwargs):
    session, auth_plugin = _get_keystone_session(
        config.cinder_group.name)

    return cinder_client.Client(
        session=session, auth=auth_plugin,
        region_name=config.CONF[
            config.cinder_group.name].region_name,
        version=2)


def get_k8s_client():
    def _check_file_exist(file_path):
        if not os.path.exists(file_path):
            raise RuntimeError(
                _("Unable to find file: %s") % file_path)

    k8s_config = k8s_client.configuration
    local_k8s_config = config.CONF[config.kubernetes_group.name]

    k8s_config.host = local_k8s_config.api_root
    k8s_config.cert_file = local_k8s_config.ssl_client_crt_file
    k8s_config.key_file = local_k8s_config.ssl_client_key_file
    k8s_config.ssl_ca_cert = local_k8s_config.ssl_ca_crt_file
    k8s_config.verify_ssl = local_k8s_config.ssl_verify_server_crt

    token_file = local_k8s_config.token_file
    if token_file:
        _check_file_exist(token_file)
        with open(token_file, 'r') as f:
            k8s_config.api_key['authorization'] = f.readline().rstrip('\n')
        k8s_config.api_key_prefix['authorization'] = 'Bearer'
    else:
        if k8s_config.cert_file:
            _check_file_exist(k8s_config.cert_file)

        if k8s_config.key_file:
            _check_file_exist(k8s_config.key_file)

        if k8s_config.verify_ssl:
            if not k8s_config.ssl_ca_cert:
                raise RuntimeError(
                    _("ssl_ca_crt_file cannot be None"))
            _check_file_exist(k8s_config.ssl_ca_cert)

    return k8s_client.CoreV1Api()
