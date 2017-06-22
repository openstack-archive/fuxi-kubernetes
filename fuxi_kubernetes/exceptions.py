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


class InvalidVolumeDriverCmdParameter(FuxiKubernetesException):
    def __init__(self, reason):
        super(InvalidVolumeDriverCmdParameter, self).__init__(
            "Invalid FlexVolume driver cmd parameter, reason:%s" % reason)


class LoadVolumeDriverException(FuxiKubernetesException):
    def __init__(self, reason):
        super(LoadVolumeDriverException, self).__init__(
            "Load volume driver failed, reason: %s" % reason)


class GetCinderVolumeException(FuxiKubernetesException):
    def __init__(self, volume_id, reason):
        super(GetCinderVolumeException, self).__init__(
            "Get Cinder volume:(%s) failed, reason: %s" % (volume_id, reason))


class AttachCinderVolumeException(FuxiKubernetesException):
    def __init__(self, volume_name, volume_id, reason):
        super(AttachCinderVolumeException, self).__init__(
            'Attach volume named:(%s) by Cinder volume:(%s) failed, '
            'reason: %s' % (volume_name, volume_id, reason))


class DetachCinderVolumeException(FuxiKubernetesException):
    def __init__(self, volume_name, volume_id, reason):
        super(DetachCinderVolumeException, self).__init__(
            'Detach volume nameed:(%s) which was attached from Cinder '
            'volume:(%s) failed, reason:%s' % (
                volume_name, volume_id, reason))


class NotSupportedCommand(FuxiKubernetesException):
    def __init__(self):
        super(NotSupportedCommand, self).__init__('Not supported')


class NotMatchedHost(FuxiKubernetesException):
    def __init__(self, expect_host_name, actual_host_name):
        super(NotMatchedHost, self).__init__(
            'Expect running on:%s, but receive the host name:%s' % (
                expect_host_name, actual_host_name))
