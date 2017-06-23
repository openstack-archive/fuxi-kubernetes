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

from oslo_serialization import jsonutils
import requests

from fuxi_kubernetes.common import constants
from fuxi_kubernetes import exceptions


class Result(object):
    __slots__ = ('status', 'message', 'device', 'volumeName', 'attached')

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.__slots__:
                setattr(self, k, v)

    def __call__(self):
        return {
            k: getattr(self, k)
            for k in self.__slots__ if hasattr(self, k)
        }


class BaseVolumeDriver(object):

    Default_Result = Result(status=constants.STATUS_NOT_SUPPORT)

    def __init__(self):
        self._driver_server_ip = ''
        self._driver_server_port = ''
        self._driver_name = ''

    def init(self):
        return Result(status=constants.STATUS_SUCCESS)

    def get_volume_name(self, **kwargs):
        return self.Default_Result

    def is_attached(self, host_name, **kwargs):
        return self.Default_Result

    def attach(self, host_name, **kwargs):
        return self.Default_Result

    def wait_for_attach(self, device_path, **kwargs):
        return self.Default_Result

    def mount_device(self, device_mount_path, device_path, **kwargs):
        return self.Default_Result

    def detach(self, device_path, host_name):
        return self.Default_Result

    def wait_for_detach(self, device_path):
        return self.Default_Result

    def unmount_device(self, device_mount_path):
        return self.Default_Result

    def mount(self, mount_dir, **kwargs):
        return self.Default_Result

    def unmount(self, mount_dir):
        return self.Default_Result

    def _request_server(self, api, data):

        def _send_and_receive():
            try:
                url = 'http://%(ip)s:%(port)d%(api)s' % (
                    {'ip': self._driver_server_ip,
                     'port': self._driver_server_port,
                     'api': api})
                data['driver'] = self._driver_name
                response = requests.post(url, json=data)
                if not response.ok:
                    return False, {'message': response.text}

                return True, response.json()

            except Exception as ex:
                return (False,
                        {'message': 'Some exception:(%s) happened '
                                    'during request to server' % str(ex)})

        ret, info = _send_and_receive()
        info['status'] = constants.STATUS_SUCCESS if ret else (
            constants.STATUS_FAILURE)
        return Result(**info)

    def __call__(self, argv):
        if not argv or len(argv) < 3:
            return self.Default_Result

        cmd = argv[2]
        if cmd not in constants.VOLUME_DRIVER_CMD:
            return self.Default_Result

        self._driver_server_ip = argv[0]
        self._driver_server_port = int(argv[1])
        argv = argv[3:]

        def _load_json_param(param):
            try:
                return jsonutils.loads(param)
            except Exception as ex:
                raise exceptions.VolumeDriverCmdArgInvalid(
                    "can not load json argument, except: %s" % ex)

        try:
            miss_arg = exceptions.VolumeDriverCmdArgInvalid("miss arguments")

            if cmd == constants.CMD_INIT:
                return self.init()

            elif cmd == constants.CMD_GET_VOLUME_NAME:
                if len(argv) != 1:
                    raise miss_arg
                return self.get_volume_name(
                    **(_load_json_param(argv[0])))

            elif cmd == constants.CMD_IS_ATTACHED:
                if len(argv) != 2:
                    raise miss_arg
                return self.is_attached(
                    argv[1], **(_load_json_param(argv[0])))

            elif cmd == constants.CMD_ATTACH:
                if len(argv) != 2:
                    raise miss_arg
                return self.attach(
                    argv[1], **(_load_json_param(argv[0])))

            elif cmd == constants.CMD_WAIT_FOR_ATTACH:
                if len(argv) != 2:
                    raise miss_arg
                return self.wait_for_attach(
                    argv[0], **(_load_json_param(argv[1])))

            elif cmd == constants.CMD_MOUNT_DEVICE:
                if len(argv) != 3:
                    raise miss_arg
                return self.mount_device(
                    argv[0], argv[1], **(_load_json_param(argv[2])))

            elif cmd == constants.CMD_DETACH:
                if len(argv) != 2:
                    raise miss_arg
                return self.detach(*argv)

            elif cmd == constants.CMD_WAIT_FOR_DETACH:
                if len(argv) != 1:
                    raise miss_arg
                return self.wait_for_detach(*argv)

            elif cmd == constants.CMD_UNMOUNT_DEVICE:
                if len(argv) != 1:
                    raise miss_arg
                return self.unmount_device(*argv)

            elif cmd == constants.CMD_MOUNT:
                if len(argv) != 2:
                    raise miss_arg
                return self.mount(
                    argv[0], **(_load_json_param(argv[1])))

            elif cmd == constants.CMD_UNMOUNT:
                if len(argv) != 1:
                    raise miss_arg
                return self.unmount(*argv)

        except Exception as ex:
            return Result(status=constants.STATUS_FAILURE,
                          message=str(ex))
