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


PROJECT_NAME = 'fuxi-kubernetes'

LOCAL_HOST = '0.0.0.0'

KUBERNETES_API_VERSION = 'v1'

KUBERNETES_VOLUME_DYNAMICALLY_CREATED_BY_KEY = "kubernetes.io/createdby"


KUBERNETES_RESOURCE_KIND = (
    KIND_PERSISTENT_VOLUME,
) = (
    'PersistentVolume',
)


KUBERNETES_PV_CAPACITY = (
    PV_CAPACITY_STORAGE,
) = (
    'storage',
)


KUBERNETES_FLEX_VOLUME_DRIVER = (
    FLEX_VOLUME_DRIVER_CINDER,
) = (
    'openstack/cinder',
)


KUBERNETES_PV_ACCESS_MODES = (
    READ_WRITE_ONCE,
    READ_ONLY_MANY,
    READ_WRITEMANY,
) = (
    'ReadWriteOnce',
    'ReadOnlyMany',
    'ReadWriteMany'
)


WATCH_EVENT_TYPE = (
    WATCH_EVENT_TYPE_ADDED,
    WATCH_EVENT_TYPE_MODIFIED,
    WATCH_EVENT_TYPE_DELETED,
    WATCH_EVENT_TYPE_ERROR,
    WATCH_EVENT_TYPE_SYNC,
) = (
    "ADDED",
    'MODIFIED',
    "DELETED",
    'ERROR',
    "SYNC",
)


VOLUME_DRIVER_CMD = (
    CMD_INIT,
    CMD_GET_VOLUME_NAME,
    CMD_IS_ATTACHED,
    CMD_ATTACH,
    CMD_WAIT_FOR_ATTACH,
    CMD_MOUNT_DEVICE,
    CMD_DETACH,
    CMD_WAIT_FOR_DETACH,
    CMD_UNMOUNT_DEVICE,
    CMD_MOUNT,
    CMD_UNMOUNT
) = (
    "init",
    "getvolumename",
    "isattached",
    "attach",
    "waitforattach",
    "mountdevice",
    "detach",
    "waitfordetach",
    "unmountdevice",
    "mount",
    "unmount",
)


VOLUME_DRIVER_CMD_OPT_ARG = (
    ARG_FSTYPE,
    ARG_RW,
    ARG_SECRET,
    ARG_FSGROUP,
    ARG_MOUNTS_DIR,
    ARG_PV_OR_VOLUME_NAME,
) = (
    "kubernetes.io/fsType",
    "kubernetes.io/readwrite",
    "kubernetes.io/secret",
    "kubernetes.io/fsGroup",
    "kubernetes.io/mountsDir",
    "kubernetes.io/pvOrVolumeName",
)


VOLUME_DRIVER_CMD_RESULT_STATUS = (
    STATUS_SUCCESS,
    STATUS_FAILURE,
    STATUS_NOT_SUPPORT
) = (
    'Success',
    'Failed',
    'Not supported',
)


VOLUME_DRIVER_TYPE = (
    VOLUME_DRIVER_CINDER,
    VOLUME_DRIVER_MANICLA,
) = (
    'Cinder',
    'Manila'
)


VOLUME_DRIVER_SERVER_API = (
    SERVER_API_IS_ATTACHED,
    SERVER_API_ATTACH,
    SERVER_API_WAIT_FOR_ATTACH,
    SERVER_API_MOUNT_DEVICE,
    SERVER_API_DETACH,
    SERVER_API_WAIT_FOR_DETACH,
    SERVER_API_UNMOUNT_DEVICE,
    SERVER_API_MOUNT,
    SERVER_API_UNMOUNT
) = (
    '/VolumeDriver.is_attached',
    '/VolumeDriver.attach',
    '/VolumeDriver.wait_for_attach',
    '/VolumeDriver.mount_device',
    '/VolumeDriver.detach',
    '/VolumeDriver.wait_for_detach',
    '/VolumeDriver.unmount_device',
    '/VolumeDriver.mount',
    '/VolumeDriver.unmount',
)


CINDER_VOLUME_ATTR_KEY = (
    CINDER_VOLUME_ATTR_VOLUME_ID,
) = (
    'VolumeID',
)
