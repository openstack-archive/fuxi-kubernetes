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

"""Server of FlexVolume driver"""

import flask
import functools
from oslo_log import log as logging
from stevedore import extension

from fuxi_kubernetes.common import config
from fuxi_kubernetes.common import constants
from fuxi_kubernetes import exceptions
from fuxi_kubernetes.flex_volume_drivers.drivers import base

LOG = logging.getLogger(__name__)

APP = flask.Flask(__name__)


def start(host=None, port=None, debug=None, **options):
    APP.run(host, port, debug, **options)


def init_volume_drivers():
    mgr = extension.ExtensionManager(
        namespace='flex_volume_drivers.server',
    )
    host_platform = config.CONF[
        config.flexvolume_driver_group.name].host_platform
    APP.volume_drivers = {
        e.name: e.plugin(host_platform)
        for e in mgr
        if e.plugin.is_support_host_platform(host_platform)
    }

    if not APP.volume_drivers:
        raise exceptions.LoadVolumeDriverException('No driver is loaded')


def api_wrapper(f):
    def _response(ret, info):
        if ret:
            info.setdefault('status', constants.STATUS_SUCCESS)
        else:
            info = {'status': constants.STATUS_FAILURE, 'message': info}
        return flask.jsonify(base.Result(**info)())

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        data = flask.request.get_json(force=True)
        driver_name = data.pop('driver', '')
        driver = APP.volume_drivers.get(driver_name)
        if not driver:
            return _response(
                False, 'Unknow FlexVolume driver:(%s)' % driver_name)

        try:
            return _response(True, f(driver, data))
        except exceptions.NotSupportedCommand:
            return _response(True, {'status': constants.STATUS_NOT_SUPPORT})
        except Exception as ex:
            return _response(False, str(ex))

    return wrapper


@APP.route(constants.SERVER_API_IS_ATTACHED, methods=['POST'])
@api_wrapper
def is_attached(driver=None, params=None):
    return {'attached': driver.is_attached(**params)}


@APP.route(constants.SERVER_API_ATTACH, methods=['POST'])
@api_wrapper
def attach(driver=None, params=None):
    return {'device': driver.attach(**params)}


@APP.route(constants.SERVER_API_WAIT_FOR_ATTACH, methods=['POST'])
@api_wrapper
def wait_for_attach(driver=None, params=None):
    return {'device': driver.wait_for_attach(**params)}


@APP.route(constants.SERVER_API_MOUNT_DEVICE, methods=['POST'])
@api_wrapper
def mount_device(driver=None, params=None):
    driver.mount_device(**params)
    return {}


@APP.route(constants.SERVER_API_DETACH, methods=['POST'])
@api_wrapper
def detach(driver=None, params=None):
    driver.detach(**params)
    return {}


@APP.route(constants.SERVER_API_WAIT_FOR_DETACH, methods=['POST'])
@api_wrapper
def wait_for_detach(driver=None, params=None):
    driver.wait_for_detach(**params)
    return {}


@APP.route(constants.SERVER_API_UNMOUNT_DEVICE, methods=['POST'])
@api_wrapper
def unmount_device(driver=None, params=None):
    driver.unmount_device(**params)
    return {}


@APP.route(constants.SERVER_API_MOUNT, methods=['POST'])
@api_wrapper
def mount(driver=None, params=None):
    driver.mount(**params)
    return {}


@APP.route(constants.SERVER_API_UNMOUNT, methods=['POST'])
@api_wrapper
def unmount(driver=None, params=None):
    driver.unmount(**params)
    return {}
