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
from keystoneauth1 import exceptions as ka_exception
from keystoneauth1.session import Session
from keystoneclient.auth import get_plugin_class
from kuryr.lib import utils as kuryr_utils
from os_brick.initiator import connector
from oslo_log import log as logging
import socket

from fuxi_kubernetes.common import config as fuxi_k8s_config

LOG = logging.getLogger(__name__)


def get_root_helper():
    return 'sudo fuxi-k8s-rootwrap %s' % fuxi_k8s_config.CONF.rootwrap_config


def brick_get_connector_properties(multipath=False, enforce_multipath=False):
    """Wrapper to automatically set root_helper in brick calls.

    :param multipath: A boolean indicating whether the connector can
                      support multipath.
    :param enforce_multipath: If True, it raises exception when multipath=True
                              is specified but multipathd is not running.
                              If False, it falls back to multipath=False
                              when multipathd is not running.
    """
    return connector.get_connector_properties(
        get_root_helper(), fuxi_k8s_config.CONF.my_ip,
        multipath, enforce_multipath)


def brick_get_connector(protocol, driver=None, use_multipath=False,
                        device_scan_attempts=3, *args, **kwargs):
    """Wrapper to get a brick connector object.

    This automatically populates the required protocol as well
    as the root_helper needed to execute commands.
    """

    root_helper = get_root_helper()
    if protocol.upper() == "RBD":
        kwargs['do_local_attach'] = True
    return connector.InitiatorConnector.factory(
        protocol, root_helper, driver=driver,
        use_multipath=use_multipath,
        device_scan_attempts=device_scan_attempts,
        *args, **kwargs)


def get_local_hostname():
    return socket.gethostname().lower()


def _openstack_auth_from_config(**config):
    plugin_class = None
    if config.get('username') and config.get('password'):
        plugin_class = get_plugin_class('password')
    else:
        plugin_class = get_plugin_class('token')

    plugin_kwargs = {
        option.dest: config[option.dest]
        for option in plugin_class.get_options()
        if option.dest in config
    }
    return plugin_class(**plugin_kwargs)


def _get_legacy_keystone_session(**kwargs):
    keystone_conf = fuxi_k8s_config.CONF.keystone
    config = {
        'auth_url': keystone_conf.auth_url,
        'username': keystone_conf.admin_user,
        'password': keystone_conf.admin_password,
        'tenant_name': keystone_conf.admin_tenant_name,
        'token': keystone_conf.admin_token,
    }
    config.update(kwargs)

    if keystone_conf.auth_insecure:
        verify = False
    else:
        verify = keystone_conf.auth_ca_cert

    return Session(auth=_openstack_auth_from_config(**config), verify=verify)


def _get_keystone_session(conf_group, **kwargs):
    try:
        auth_plugin = kuryr_utils.get_auth_plugin(conf_group)
        session = kuryr_utils.get_keystone_session(conf_group, auth_plugin)
        return session, auth_plugin
    except ka_exception.MissingRequiredOptions:
        return _get_legacy_keystone_session(**kwargs), None


def get_cinder_client(*args, **kwargs):
    session, auth_plugin = _get_keystone_session(
        fuxi_k8s_config.cinder_group.name)
    return cinder_client.Client(
        session=session, auth=auth_plugin,
        region_name=fuxi_k8s_config.CONF.cinder.region_name,
        version=2)
