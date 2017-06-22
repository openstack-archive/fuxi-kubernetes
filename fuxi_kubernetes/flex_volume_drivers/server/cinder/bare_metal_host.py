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

import functools
import os
from oslo_log import log as logging

from fuxi_kubernetes import exceptions
from fuxi_kubernetes.flex_volume_drivers.server import utils

LOG = logging.getLogger(__name__)


def check_host_name(f):

    @functools.wraps(f)
    def wrapper(self, host_name, *args, **kwargs):
        if not host_name:
            host_name = self.host_name
        elif host_name != self.host_name:
            raise exceptions.NotMatchedHostExcept(self.host_name, host_name)
        return f(self, host_name, *args, **kwargs)

    return wrapper


class BareMetalHost(object):
    def __init__(self, cinder_client):
        self._cinder_client = cinder_client
        self._host_name = utils.get_local_hostname()
        self._attached_volumes = {}

    @property
    def host_name(self):
        return self._host_name

    @check_host_name
    def is_attached(self, host_name, volume):
        for item in volume.attachments:
            LOG.debug("Check whether the volume is attached on host:(%s), "
                      "check attachment:%s", host_name, str(item))
            if host_name != item['host_name']:
                continue
            if os.path.exists(item['device']):
                return True
        return False

    @check_host_name
    def attach(self, host_name, volume):
        volume_id = volume.id

        # reserve volume
        try:
            self._cinder_client.volumes.reserve(volume)
        except Exception as ex:
            LOG.error("Reserve Cinder volume:(%s) failed, reason:%s",
                      volume, str(ex))
            raise exceptions.AttachCinderVolumeExcept(
                volume_id, 'Reserve volume failed ')

        # initialize connect
        conn_info = None
        try:
            conn_info = self._cinder_client.volumes.initialize_connection(
                volume_id, utils.brick_get_connector_properties())
        except Exception as ex:
            LOG.error("Initialize connection to Cinder volume:(%s) failed, "
                      "reason:%s", volume, str(ex))

            try:
                self._cinder_client.volumes.unreserve(volume)
            except Exception as ex:
                LOG.error("Unreserve Cinder volume:(%s) failed, reason:%s",
                          volume, str(ex))

            raise exceptions.AttachCinderVolumeExcept(
                volume_id, 'Initialize connection failed ')

        # connect volume
        connector = utils.brick_get_connector(conn_info['driver_volume_type'])
        device_info = connector.connect_volume(conn_info['data'])
        path = os.path.realpath(device_info['path'])

        # set attachment
        try:
            self._cinder_client.volumes.attach(
                volume=volume, instance_uuid=None, mountpoint=path,
                host_name=host_name)
        except Exception as ex:
            LOG.error("Set attachment info to Cinder failed,")

            try:
                connector.disconnect_volume(conn_info['data'], None)
                self._cinder_client.volumes.unreserve(volume)
            except Exception as ex:
                LOG.error("Disconnect or unreserve volume:(%s) failed, "
                          "reason:%s", volume, str(ex))

            raise exceptions.AttachCinderVolumeExcept(
                volume_id, "Set attachment info to Cinder failed,")

        self._attached_volumes[path] = volume_id
        return path

    def wait_for_attach(self, device_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportCommandExcept()

    def mount_device(self, device_mount_path, device_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportCommandExcept()

    @check_host_name
    def detach(self, host_name, device_path):
        if not os.path.exists(device_path):
            LOG.warn('Detach device:(%s), the device is not exist',
                     device_path)
            return

        volume_id = self._get_volume_id_by_device_path(device_path)
        if not volume_id:
            raise exceptions.DetachCinderVolumeExcept(
                device_path, '', 'Can not find volume id')
        volume = None
        try:
            volume = self._cinder_client.volumes.get(volume_id)
        except Exception as ex:
            raise exceptions.DetachCinderVolumeExcept(
                device_path, volume_id, 'Get volume from Cinder failed')

        conn_info = None
        try:
            conn_info = self._cinder_client.volumes.initialize_connection(
                volume_id, utils.brick_get_connector_properties())
        except Exception as ex:
            LOG.error("Initialize connection to Cinder volume:(%s) failed, "
                      "reason:%s", volume_id, str(ex))

            raise exceptions.DetachCinderVolumeExcept(
                device_path, volume_id, 'Initialize connection failed')

        # disconnect volume
        connector = utils.brick_get_connector(conn_info['driver_volume_type'])
        connector.disconnect_volume(conn_info['data'], None)

        # delete attachment
        try:
            for am in volume.attachments:
                if am['host_name'].lower() == host_name:
                    self._cinder_client.volumes.detach(
                        volume_id, attachment_uuid=am['attachment_id'])
                    break
            else:
                LOG.warn("Detach device:(%s), does not find the attachment of "
                         "wolume:(%s) which is attached on host:(%s)",
                         device_path, volume_id, host_name)
        except Exception as ex:
            LOG.error("Detach device:(%s), delete attachment from Cinder "
                      "failed, reason:%s", device_path, str(ex))
            raise exceptions.DetachCinderVolumeExcept(
                device_path, volume_id,
                'Delete attachment info from Cinder failed,')

    def wait_for_detach(self, device_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportCommandExcept()

    def unmount_device(self, device_mount_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportCommandExcept()

    def mount(self, mount_dir):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportCommandExcept()

    def unmount(self, mount_dir):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportCommandExcept()

    def _get_volume_id_by_device_path(self, device_path):
        volume_id = self._attached_volumes.get(device_path)
        if volume_id:
            return volume_id
