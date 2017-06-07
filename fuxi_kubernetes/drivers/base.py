#!/usr/bin/env python
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_serialization import jsonutils

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

    Default_Result = Result(status=constants.RESULT_NOT_SUPPORT)

    def init(self):
        return Result(status=constants.RESULT_SUCCESS)

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

    def __call__(self, argv):
        if not argv:
            return self.Default_Result

        cmd = argv[0]
        if cmd not in constants.VOLUME_DRIVER_CMD:
            return self.Default_Result

        def _load_json_param(param):
            try:
                return jsonutils.loads(param)
            except Exception as ex:
                raise exceptions.VolumeDriverCmdArgInvalid(
                    "can not load json argument, except: %s" % ex)

        try:
            miss_arg = exceptions.VolumeDriverCmdArgInvalid("miss arguments")
            argv = argv[1:]

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
            return Result(status=constants.RESULT_FAILURE,
                          message=str(ex))
