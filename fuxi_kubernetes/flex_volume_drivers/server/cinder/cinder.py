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


class ServerCinder(object):
    # TODO(zengchen): implement all the interface of driver, such as
    # is_attached, attach, detach, mount, unmount etc.

    def __init__(self, host_platform):
        self._cinder_client = None
        self._host = None

    def is_attached(self, volume_id, host_name, **kwargs):
        return False

    @classmethod
    def is_support_host_platform(cls, host_platform):
        return True
