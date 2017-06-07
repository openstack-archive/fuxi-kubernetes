#!/bin/sh
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


err() {
    echo -ne $* 1>&2
}


log() {
    echo -ne $* >&1
}


usage() {
    err "Invalid usage. Usage: "
    err "\t$0 init"
    err "\t$0 getvolumename <json params>"
    err "\t$0 isattached <json params> <nodename>"
    err "\t$0 attach <json params> <nodename>"
    err "\t$0 waitforattach <mount device> <json params>"
    err "\t$0 mountdevice <mount dir> <mount device> <json params>"
    err "\t$0 detach <mount device> <nodename>"
    err "\t$0 waitfordetach <mount device>"
    err "\t$0 unmountdevice <mount device>"
    err "\t$0 mount <mount dir> <json params>"
    err "\t$0 unmount <mount dir>"
    exit 1
}


if [ $# -lt 1 ]; then
    usage
fi

out=`python fuxi-k8s-volume-driver-manila $*`
code=$?
if [ $code -eq 0 ]; then
    log "$out"
else
    err "$out"
fi
exit $code
