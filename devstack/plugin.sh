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


function create_account {
    create_service_user "$FK_SERVICE_NAME" "admin"
    get_or_create_service "$FK_SERVICE_NAME" "$FK_SERVICE_TYPE" "Kubernetes FlexVolume plugin based on Cinder/Manila"
}

function create_cache_dir {
    sudo rm -rf $FK_AUTH_CACHE_DIR
    sudo mkdir -p $FK_AUTH_CACHE_DIR
    sudo chown $(whoami) $FK_AUTH_CACHE_DIR

}

function do_configure {
    sudo install -o $STACK_USER -d $FK_CONF_DIR
    (exec $FK_CODE_DIR/tools/generate_config_file_samples.sh)
    sudo cp $FK_CODE_DIR/etc/fuxi_kubernetes.conf.sample $FK_MAIN_CONF_FILE

    sudo cp $FK_CODE_DIR/etc/rootwrap.conf $FK_CONF_DIR
    sudo cp $FK_CODE_DIR/etc/rootwrap.d $FK_CONF_DIR -fr

    iniset $FK_MAIN_CONF_FILE DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
    iniset $FK_MAIN_CONF_FILE DEFAULT use_syslog $SYSLOG
    setup_colorized_logging $FK_MAIN_CONF_FILE

    iniset $FK_MAIN_CONF_FILE flexvolume_driver node_ip $HOST_IP

    create_cache_dir
    configure_auth_token_middleware $FK_MAIN_CONF_FILE $FK_SERVICE_NAME $FK_AUTH_CACHE_DIR cinder
}

if is_service_enabled fuxi-kubernetes; then

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo "$FK_SERVICE_NAME Installing"
        setup_package $FK_CODE_DIR -e

    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo "$FK_SERVICE_NAME Configuring"
        do_configure

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo "$FK_SERVICE_NAME Creating an entity to auth service"
        create_account

        if is_service_enabled fuxi-k8s-volume-driver-server; then
           run_process fuxi-k8s-volume-driver-server "$FK_BIN_DIR/fuxi-k8s-volume-driver-server --config-file $FK_MAIN_CONF_FILE"
        fi

        if is_service_enabled fuxi-k8s-volume-provisioner; then
           run_process fuxi-k8s-volume-provisioner "$FK_BIN_DIR/fuxi-k8s-volume-provisioner --config-file $FK_MAIN_CONF_FILE"
        fi

    fi

    if [[ "$1" == "unstack" ]]; then
        if is_service_enabled fuxi-k8s-volume-driver-server; then
           stop_process fuxi-k8s-volume-driver-server
        fi

        if is_service_enabled fuxi-k8s-volume-provisioner; then
           stop_process fuxi-k8s-volume-provisioner
        fi
    fi
fi
