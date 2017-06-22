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
from oslo_log import log as logging

from fuxi_kubernetes import exceptions
from fuxi_kubernetes.flex_volume_drivers.service import utils

LOG = logging.getLogger(__name__)


class BareMetalHost(object):
    def __init__(self, cinder_client):
        self._cinder_client = cinder_client
        self._host_name = utils.get_local_hostname()

    def attach(self, volume, host_name):
        try:
            self._cinder_client.volumes.reserve(volume)
        except Exception as ex:
            LOG.error("Reserve Cinder volume:(%s) failed, reason:%s",
                      volume, str(ex))
            raise exceptions.AttachCinderVolumeExcept(
                volume.id, 'Reserve volume failed ')

        conn_info = None
        try:
            conn_info = self._cinder_client.volumes.initialize_connection(
                volume.id, utils.brick_get_connector_properties())
        except Exception as ex:
            LOG.error("Initialize connection to Cinder volume:(%s) failed, "
                      "reason:%s", volume, str(ex))
            raise exceptions.AttachCinderVolumeExcept(
                volume.id, 'Initialize connection failed ')

        connector = utils.brick_get_connector(conn_info['driver_volume_type'])
        device_info = connector.connect_volume(conn_info['data'])

        try:
            self._cinder_client.volumes.attach(
                volume=volume, instance_uuid=None, mountpoint=None,
                host_name=self._host_name)
        except Exception as ex:
            try:
                connector.disconnect_volume(conn_info['data'], None)
                self._cinder_client.volumes.unreserve(volume)
            except Exception:
                pass

            LOG.error("Set attachment info to Cinder failed,")
            raise exceptions.AttachCinderVolumeExcept(
                volume.id, "Set attachment info to Cinder failed,")

        return os.path.realpath(device_info['path'])

    def is_attached(self, volume, host_name):
        if not host_name:
            host_name = self._host_name

        return host_name in [item['host_name'] for item in volume.attachments]
