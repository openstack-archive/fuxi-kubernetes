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
    ARG_MOUNTS_DIR
) = (
    "kubernetes.io/fsType",
    "kubernetes.io/readwrite",
    "kubernetes.io/secret",
    "kubernetes.io/fsGroup",
    "kubernetes.io/mountsDir",

)


VOLUME_DRIVER_CMD_RESULT = (
    RESULT_SUCCESS,
    RESULT_FAILURE,
    RESULT_NOT_SUPPORT
) = (
    'Success',
    'Failed',
    'Not supported',
)
