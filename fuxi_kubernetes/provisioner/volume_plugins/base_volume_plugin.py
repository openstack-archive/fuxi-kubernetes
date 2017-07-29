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

"""Base provision plugin"""

from abc import ABCMeta
from abc import abstractmethod
from collections import namedtuple
import six

# Option for provisioning pv
# :param pv_reclaim_policy: string
# :param pv_name: string
# :param pvc: kubernetes.client.V1PersistentVolumeClaim
# :param parameters: dict
VolumeOption = namedtuple(
    "VolumeOption", ['pv_reclaim_policy', 'pv_name', 'pvc', 'parameters'])


@six.add_metaclass(ABCMeta)
class BaseVolumePlugin(object):

    @abstractmethod
    def provision(self, volume_option):
        """Provision a new pv

        :param volume_option: VolumeOption
        :returns: kubernetes.client.V1PersistentVolume
        """

    @abstractmethod
    def delete(slef, pv):
        """Delete a pv

        :param pv: kubernetes.client.V1PersistentVolume
        """
