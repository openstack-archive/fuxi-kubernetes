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
from os_brick.initiator import connector
import socket

from fuxi_kubernetes.common import config as local_config


def get_root_helper():
    return 'sudo fuxi-k8s-rootwrap %s' % local_config.CONF[
        local_config.flexvolume_driver_group.name].rootwrap_config


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
        get_root_helper(),
        local_config.CONF[local_config.flexvolume_driver_group.name].node_ip,
        multipath, enforce_multipath)


def brick_get_connector(protocol, driver=None, use_multipath=False,
                        device_scan_attempts=3, *args, **kwargs):
    """Wrapper to get a brick connector object.

    This automatically populates the required protocol as well
    as the root_helper needed to execute commands.
    """

    if protocol.upper() == "RBD":
        kwargs['do_local_attach'] = True

    return connector.InitiatorConnector.factory(
        protocol, get_root_helper(),
        driver=driver, use_multipath=use_multipath,
        device_scan_attempts=device_scan_attempts,
        *args, **kwargs)


def get_local_hostname():
    return socket.gethostname().lower()


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
