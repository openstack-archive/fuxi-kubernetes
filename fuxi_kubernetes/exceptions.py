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


class FuxiKubernetesException(Exception):
    """Default Fuxi-kubernetes exception"""


class VolumeDriverCmdArgInvalid(FuxiKubernetesException):
    def __init__(self, reason):
        super(VolumeDriverCmdArgInvalid, self).__init__(
            "Invalid volume driver cmd argument, reason: %s" % reason)


class LoadVolumeDriverExcept(FuxiKubernetesException):
    def __init__(self, reason):
        super(LoadVolumeDriverExcept, self).__init__(
            "Load volume driver failed, reason: %s" % reason)


class GetCinderVolumeExcept(FuxiKubernetesException):
    def __init__(self, volume_id, reason):
        super(GetCinderVolumeExcept, self).__init__(
            "Get Cinder volume:(%s) failed, reason: %s" % (volume_id, reason))


class AttachCinderVolumeExcept(FuxiKubernetesException):
    def __init__(self, volume_id, reason):
        super(AttachCinderVolumeExcept, self).__init__(
            'Attach Cinder volume:(%s) failed, '
            'reason: %s' % (volume_id, reason))


class NotSupportCommandExcept(FuxiKubernetesException):
    def __init__(self):
        super(NotSupportCommandExcept, self).__init__('Not supported')


class DetachCinderVolumeExcept(FuxiKubernetesException):
    def __init__(self, device_path, volume_id, reason):
        super(DetachCinderVolumeExcept, self).__init__(
            'Detach device:(%s) binded to Cinder volume:(%s) failed, '
            'reason: %s' % (device_path, volume_id, reason))


class NotMatchedHostExcept(FuxiKubernetesException):
    def __init__(self, expect_host_name, actual_host_name):
        super(NotMatchedHostExcept, self).__init__(
            'Expect running on:%s, but receive the host name:%s' % (
                expect_host_name, actual_host_name))
