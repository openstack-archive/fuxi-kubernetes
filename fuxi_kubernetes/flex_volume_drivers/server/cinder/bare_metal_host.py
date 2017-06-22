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
import re

from fuxi_kubernetes import exceptions
from fuxi_kubernetes.flex_volume_drivers.server import utils

LOG = logging.getLogger(__name__)


def check_host_name(f):

    @functools.wraps(f)
    def wrapper(self, host_name, *args, **kwargs):
        if not host_name:
            host_name = self.host_name
        else:
            host_name = host_name.lower()

        if host_name != self.host_name:
            raise exceptions.NotMatchedHost(self.host_name, host_name)
        return f(self, host_name, *args, **kwargs)

    return wrapper


def log_error(prefix, info, *args):
    LOG.error('%s, %s' % (prefix, info), *args)


class BareMetalHost(object):
    def __init__(self, cinder_client):
        self._cinder_client = cinder_client
        self._host_name = utils.get_local_hostname()
        self._attached_volumes = {}
        self._volume_link_dir = '/dev/disk/by-id/'

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
    def attach(self, host_name, volume, pv_or_volume_name):

        _log_error = functools.partial(
            log_error, 'Attach volume:(%s)' % pv_or_volume_name)

        def _raise_except(reason):
            raise exceptions.AttachCinderVolumeException(
                pv_or_volume_name, volume_id, reason)

        phase_init_connect = 0
        phase_connect_volume = 1
        phase_create_link = 2
        phase_set_attachment = 3

        def _rollback(phase):
            try:
                if phase >= phase_set_attachment:
                    utils.execute("rm", "-f", link_to_device)

                if phase >= phase_create_link:
                    connector.disconnect_volume(conn_info['data'], None)

                if phase >= phase_init_connect:
                    self._cinder_client.volumes.unreserve(volume)

            except Exception as ex:
                _log_error('try to roolback the operation of attach on phase '
                           'of (%d) failed, reason:%s', phase, str(ex))

        volume_id = volume.id

        if self._search_volume_ids(pv_or_volume_name):
            _log_error('reduplicative pv/volume name:%s', pv_or_volume_name)
            _raise_except(
                'reduplicative pv/volume name:%s' % pv_or_volume_name)

        # reserve volume
        try:
            self._cinder_client.volumes.reserve(volume)
        except Exception as ex:
            _log_error("reserve Cinder volume:(%s) failed, reason:%s",
                       volume_id, str(ex))
            _raise_except('reserve volume failed')

        # initialize connect
        conn_info = None
        try:
            conn_info = self._cinder_client.volumes.initialize_connection(
                volume_id, utils.brick_get_connector_properties())
        except Exception as ex:
            _rollback(phase_init_connect)
            _log_error("initialize connection to Cinder volume:(%s) failed, "
                       "reason:%s", volume_id, str(ex))
            _raise_except('initialize connection failed ')

        # connect volume
        connector = None
        path = ''
        try:
            connector = utils.brick_get_connector(
                conn_info['driver_volume_type'])
            device_info = connector.connect_volume(conn_info['data'])
            path = os.path.realpath(device_info['path'])
        except Exception as ex:
            _rollback(phase_connect_volume)
            _log_error("connect to Cinder volume:(%s) failed, reason:%s",
                       volume_id, str(ex))
            _raise_except('connect to Cinder volume failed')

        # create soft link to device
        link_to_device = self._link_to_device(volume.id, pv_or_volume_name)
        try:
            utils.execute_cmd('ln', '-s', path, link_to_device)
        except Exception as ex:
            _rollback(phase_create_link)
            _log_error("create soft link:(%s) to device:(%s) failed, "
                       "reason:%s.", link_to_device, path, str(ex))
            _raise_except("create soft link to device failed")

        # set attachment
        try:
            self._cinder_client.volumes.attach(
                volume=volume, instance_uuid=None, mountpoint=path,
                host_name=host_name)
        except Exception as ex:
            _rollback(phase_set_attachment)
            _log_error("set attachment info to Cinder volume:(%s) failed,",
                       volume_id)
            _raise_except("set attachment info to Cinder failed,")

        self._attached_volumes[pv_or_volume_name] = volume_id
        return path

    def wait_for_attach(self, device_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportedCommand()

    def mount_device(self, device_mount_path, device_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportedCommand()

    @check_host_name
    def detach(self, host_name, pv_or_volume_name):

        _log_error = functools.partial(
            log_error, 'Detach volume:(%s)' % pv_or_volume_name)

        def _raise_except(reason):
            raise exceptions.DetachCinderVolumeException(
                pv_or_volume_name, volume_id, reason)

        volume_id = ''
        volume_ids = self._search_volume_ids(pv_or_volume_name)
        if not volume_ids or len(volume_ids) > 1:
            info = 'can not find corresponding volume id'
            _log_error(info)
            _raise_except(info)
        volume_id = volume_ids[0]

        volume = None
        try:
            volume = self._cinder_client.volumes.get(volume_id)
        except Exception as ex:
            _log_error('get volume:(%s) from Cinder failed', volume_id)
            _raise_except('get volume from Cinder failed')

        # delete link to device
        try:
            link_to_device = self._link_to_device(volume_id, pv_or_volume_name)
            if os.path.islink(link_to_device):
                utils.execute('rm', '-f', link_to_device)
        except Exception as ex:
            _log_error("delete link:(%s) to device:(%s) failed, reason:%s",
                       link_to_device, os.path.realpath(link_to_device),
                       str(ex))
            _raise_except('delete link to device failed')

        # disconnect volume
        conn_info = None
        try:
            conn_info = self._cinder_client.volumes.initialize_connection(
                volume_id, utils.brick_get_connector_properties())
        except Exception as ex:
            _log_error("initialize connection to Cinder volume:(%s) failed, "
                       "reason:%s", volume_id, str(ex))
            _raise_except('initialize connection failed')

        try:
            connector = utils.brick_get_connector(
                conn_info['driver_volume_type'])
            connector.disconnect_volume(conn_info['data'], None)
        except Exception as ex:
            _log_error("disconnect volume:(%s) failed, reason:%s",
                       volume_id, str(ex))
            _raise_except('disconnect volume failed')

        # delete attachment
        attachment_id = None
        for am in volume.attachments:
            if am['host_name'] == host_name:
                attachment_id = am['attachment_id']
                break
        else:
            _log_error("does not find the attachment of wolume:(%s) which "
                       "is attached on host:(%s)", volume_id, host_name)
        try:
            if attachment_id:
                self._cinder_client.volumes.detach(
                    volume_id, attachment_uuid=attachment_id)
        except Exception as ex:
            _log_error("delete attachment:(%s) from Cinder failed, reason:%s",
                       attachment_id, str(ex))
            _raise_except('delete attachment info from Cinder failed,')

        self._attached_volumes.pop(pv_or_volume_name, None)

    def wait_for_detach(self, device_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportedCommand()

    def unmount_device(self, device_mount_path):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportedCommand()

    def mount(self, mount_dir):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportedCommand()

    def unmount(self, mount_dir):
        LOG.warn('Use Kubernetes\' default method instead')
        raise exceptions.NotSupportedCommand()

    def _search_volume_ids(self, pv_or_volume_name):
        volume_id = self._attached_volumes.get(pv_or_volume_name)
        if volume_id:
            return [volume_id]

        def _volume_id(f):
            if f.find(flag) > 0 and os.path.islink(os.path.join(link_dir, f)):
                strs = re.split(flag, f)
                return strs[0] if len(strs) == 2 and strs[1] == '' else None

        flag = "_%s" % pv_or_volume_name
        link_dir = self._volume_link_dir

        volume_ids = []
        for f in os.listdir(link_dir):
            volume_id = _volume_id(f)
            if volume_id:
                volume_ids.append(volume_id)

        return volume_ids

    def _link_to_device(self, volume_id, pv_or_volume_name):
        return os.path.join(self._volume_link_dir,
                            volume_id, pv_or_volume_name)
