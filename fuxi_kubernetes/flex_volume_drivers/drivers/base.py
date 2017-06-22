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

    default_result = Result(status=constants.STATUS_NOT_SUPPORT)

    def __init__(self):
        self._driver_server_port = ''
        self._driver_name = ''

    def init(self):
        return Result(status=constants.STATUS_SUCCESS)

    def get_volume_name(self, **kwargs):
        return self.default_result

    def is_attached(self, host_name, **kwargs):
        return self.default_result

    def attach(self, host_name, **kwargs):
        return self.default_result

    def wait_for_attach(self, device_path, **kwargs):
        return self.default_result

    def mount_device(self, device_mount_path, device_path, **kwargs):
        return self.default_result

    def detach(self, pv_or_volume_name, host_name):
        return self.default_result

    def wait_for_detach(self, device_path):
        return self.default_result

    def unmount_device(self, device_mount_path):
        return self.default_result

    def mount(self, mount_dir, **kwargs):
        return self.default_result

    def unmount(self, mount_dir):
        return self.default_result

    def _generate_result(self, ret, info):
        info['status'] = constants.STATUS_SUCCESS if ret else (
            constants.STATUS_FAILURE)
        return Result(**info)

    def _request_server(self, api, data):
        def _send_and_receive():
            try:
                url = 'http://%(ip)s:%(port)d%(api)s' % {
                    'ip': constants.LOCAL_HOST,
                    'port': self._driver_server_port,
                    'api': api}
                data['driver'] = self._driver_name
                response = requests.post(url, json=data)
                if not response.ok:
                    return False, response.text

                return True, response.json()

            except Exception as ex:
                return (False,
                        'During request to server, '
                        'threw exception:(%s)' % str(ex))

        ret, info = _send_and_receive()
        if ret:
            return Result(**info)
        return Result(status=constants.STATUS_FAILURE, message=info)

    def __call__(self, argv):
        if not argv or len(argv) < 2:
            return self.default_result

        cmd = argv[1]
        if cmd not in constants.VOLUME_DRIVER_CMD:
            return self.default_result

        self._driver_server_port = int(argv[0])
        argv = argv[2:]

        cmd_info = self._get_cmd_info(cmd)
        if len(argv) != cmd_info['required_params_num']:
            return Result(
                status=constants.STATUS_FAILURE,
                message='Miss parameters, require %d parameters, '
                        'but receive %d' % (cmd_info['required_params_num'],
                                            len(argv)))
        try:
            return cmd_info['func'](argv)
        except Exception as ex:
            return Result(status=constants.STATUS_FAILURE,
                          message=str(ex))

    def _get_cmd_info(self, cmd):

        def _load_json_param(data):
            try:
                return jsonutils.loads(data)
            except Exception:
                raise exceptions.InvalidVolumeDriverCmdParameter(
                    "can not load json parameter:(%s)" % data)

        return {
            constants.CMD_INIT: {
                'required_params_num': 0,
                'func': lambda argv: self.init()
            },
            constants.CMD_GET_VOLUME_NAME: {
                'required_params_num': 1,
                'func': lambda argv: self.get_volume_name(
                    **(_load_json_param(argv[0])))
            },
            constants.CMD_IS_ATTACHED: {
                'required_params_num': 2,
                'func': lambda argv: self.is_attached(
                    argv[1], **(_load_json_param(argv[0])))
            },
            constants.CMD_ATTACH: {
                'required_params_num': 2,
                'func': lambda argv: self.attach(
                    argv[1], **(_load_json_param(argv[0])))
            },
            constants.CMD_WAIT_FOR_ATTACH: {
                'required_params_num': 2,
                'func': lambda argv: self.wait_for_attach(
                    argv[0], **(_load_json_param(argv[1])))
            },
            constants.CMD_MOUNT_DEVICE: {
                'required_params_num': 3,
                'func': lambda argv: self.mount_device(
                    argv[0], argv[1], **(_load_json_param(argv[2])))
            },
            constants.CMD_DETACH: {
                'required_params_num': 2,
                'func': lambda argv: self.detach(*argv)
            },
            constants.CMD_WAIT_FOR_DETACH: {
                'required_params_num': 1,
                'func': lambda argv: self.wait_for_detach(*argv)
            },
            constants.CMD_UNMOUNT_DEVICE: {
                'required_params_num': 1,
                'func': lambda argv: self.unmount_device(*argv)
            },
            constants.CMD_MOUNT: {
                'required_params_num': 2,
                'func': lambda argv: self.mount(
                    argv[0], **(_load_json_param(argv[1])))
            },
            constants.CMD_UNMOUNT: {
                'required_params_num': 1,
                'func': lambda argv: self.unmount(*argv)
            },
        }.get(cmd)
