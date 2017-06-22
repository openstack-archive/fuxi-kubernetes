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

import flask
import functools
from oslo_config import cfg
from oslo_log import log as logging
from stevedore import extension

from fuxi_kubernetes.common import constants
from fuxi_kubernetes import exceptions
from fuxi_kubernetes.flex_volume_drivers.drivers import base

LOG = logging.getLogger(__name__)

APP = flask.Flask(__name__)


def run(host=None, port=None, debug=None, **options):
    APP.run(host, port, debug, **options)


def init_volume_drivers():
    mgr = extension.ExtensionManager(
        namespace='flex_volume_drivers.service',
    )
    host_platform = cfg.CONF.host_platform
    APP.volume_drivers = {
        e.name: e.plugin(host_platform)
        for e in mgr
        if e.plugin.is_support_host_platform(host_platform)
    }

    if not APP.volume_drivers:
        raise exceptions.LoadVolumeDriverExcept('No driver is loaded')


def api_wrapper(f):
    def _response(ret, info):
        info['status'] = constants.STATUS_SUCCESS if ret else (
            constants.STATUS_FAILURE)
        return flask.jsonify(base.Result(**info)())

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        data = flask.request.get_json(force=True)
        driver = APP.volume_drivers.get(data.get('driver'))
        if not driver:
            return _response(
                False,
                {'message': 'Unknow volume driver:%s' % data.get('driver')})

        ret = True
        info = None
        try:
            info = f(driver, data)
        except Exception as ex:
            ret = False
            info = {'message': str(ex)}

        return _response(ret, info)

    return wrapper


@APP.route(constants.SERCIE_API_IS_ATTACHED, methods=['POST'])
@api_wrapper
def is_attached(driver=None, param=None):
    return {'attached': driver.is_attached(**param)}


@APP.route(constants.SERCIE_API_ATTACH, methods=['POST'])
@api_wrapper
def attach(driver=None, param=None):
    return {'attached': driver.attach(**param)}
