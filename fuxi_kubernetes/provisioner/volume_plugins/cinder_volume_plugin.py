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

from kubernetes import client as k8s_client

from fuxi_kubernetes.common import constants
from fuxi_kubernetes import exceptions
from fuxi_kubernetes.provisioner.volume_plugins import base_volume_plugin
from fuxi_kubernetes import utils


class CinderVolumePlugin(base_volume_plugin.BaseVolumePlugin):

    def __init__(self):
        self._cinder_client = utils.get_cinder_client()
        self._supported_volume_access_modes = [
            constants.READ_WRITE_ONCE]

    def provision(self, volume_option):
        access_modes = volume_option.pvc.spec.access_modes
        if not all([am in self._supported_volume_access_modes
                    for am in access_modes]):
            raise exceptions.CreatePersistentVolumeException(
                'Cinder volume',
                'receive invalid access modes:%s' % str(access_modes))
        if not access_modes:
            access_modes = self._supported_volume_access_modes

        if volume_option.parameters is None:
            volume_option.parameters = {}

        volume = None
        try:
            volume = self._create_volume(volume_option)
        except Exception as ex:
            raise exceptions.CreatePersistentVolumeException(
                'Cinder volume',
                'create volume failed, %s' % str(ex))

        return k8s_client.V1PersistentVolume(
            metadata=k8s_client.V1ObjectMeta(
                name=volume_option.pv_name,
                annotations={
                    constants.KUBERNETES_VOLUME_DYNAMICALLY_CREATED_BY_KEY:
                        "external-cinder-dynamic-provisioner"}
            ),
            spec=k8s_client.V1PersistentVolumeSpec(
                persistent_volume_reclaim_policy=(
                    volume_option.pv_reclaim_policy),
                access_modes=access_modes,
                capacity={
                    constants.PV_CAPACITY_STORAGE: "%dGi" % volume.size},
                flex_volume=k8s_client.V1FlexVolumeSource(
                    driver=constants.FLEX_VOLUME_DRIVER_CINDER,
                    fs_type=volume_option.parameters.get('fstype', 'ext4'),
                    options={
                        constants.CINDER_VOLUME_ATTR_VOLUME_ID: volume.id},
                    read_only=volume_option.parameters.get('read_only', False)
                )
            )
        )

    def delete(self, pv):
        """Delete a pv

        :param pv: kubernetes.client.V1PersistentVolume
        """
        volume_id = None
        try:
            volume_id = pv.spec.flex_volume.options.get(
                constants.CINDER_VOLUME_ATTR_VOLUME_ID)
            if volume_id:
                self._cinder_client.volumes.delete(volume_id)
        except Exception as ex:
            raise exceptions.DeletePersistentVolumeException(
                "Cinder volume, id=%s" % volume_id, str(ex))

    def _create_volume(self, volume_option):
        def _get_volume_size():
            try:
                size = volume_option.pvc.spec.resources.requests.get(
                    constants.PV_CAPACITY_STORAGE)
            except Exception:
                raise Exception('cat not parse volume size')

            try:
                s = int(size)
                return s >> 30 + 1
            except Exception:
                pass

            units = {'Ki': lambda d: (d >> 20) + 1,
                     'Mi': lambda d: (d >> 10) + 1,
                     'Gi': lambda d: d,
                     'Ti': lambda d: d << 10,
                     'Pi': lambda d: d << 20,
                     'Ei': lambda d: d << 30}

            unit = size[-2:] if len(size) > 2 else ""
            if unit not in units:
                raise Exception('unknown unit of volume size:%s' % size)

            try:
                return units[unit](int(size[0:len(size) - 2]))
            except Exception:
                raise Exception('can not convert volume size:%s' % size)

        params = volume_option.parameters
        return self._cinder_client.volumes.create(
            size=_get_volume_size(),
            name=volume_option.pv_name,
            volume_type=params.get('volume_type'),
            availability_zone=params.get('availability_zone')
        )
