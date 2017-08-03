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

from collections import namedtuple
import eventlet
from oslo_log import log as logging

from fuxi_kubernetes.common import constants

LOG = logging.getLogger(__name__)


ListerWatcher = namedtuple('ListerWatcher', 'list, watch')


class Reflector(object):
    def __init__(self, watch_resouce_type, lister_watcher,
                 watch_timeout, store):
        self._watch_resouce_type = watch_resouce_type
        self._lister_watcher = lister_watcher
        self._watch_timeout = watch_timeout
        self._store = store

        self._running = False
        self._event_handle = {
            constants.WATCH_EVENT_TYPE_ADDED: self._store.add,
            constants.WATCH_EVENT_TYPE_MODIFIED: self._store.update,
            constants.WATCH_EVENT_TYPE_DELETED: self._store.delete
        }

    def stop(self):
        self._running = False

    def start(self):
        def _list_and_watch():
            while self._running:
                eventlet.sleep(0.1)

                resource_version, err = self._list()
                if err:
                    continue

                while self._running:
                    eventlet.sleep(0.1)

                    events, err = self._watch(resource_version)
                    if err:
                        break

                    resource_version, err = self._watch_handler(
                        resource_version, events)
                    if err:
                        break

        self._running = True
        eventlet.spawn(_list_and_watch)

    def _list(self):
        try:
            resources = self._lister_watcher.list(resource_version=0)
            resource_version = resources.metadata.resource_version
            self._store.replace(resources.items, resource_version)
            return resource_version, None

        except Exception as ex:
            LOG.error("Reflector list resource failed, reason:%s", str(ex))
            return None, ex

    def _watch(self, resource_version):
        try:
            events = self._lister_watcher.watch(
                resource_version=resource_version,
                timeout_seconds=self._watch_timeout)
            return events, None

        except Exception as ex:
            LOG.error('Reflector watch resource failed, reason:%s', str(ex))
            return None, ex

    def _watch_handler(self, resource_version, events):
        try:
            new_resource_version = resource_version
            for e in events:
                if not self._running:
                    break

                event_type = e['type']
                if event_type == constants.WATCH_EVENT_TYPE_ERROR:
                    LOG.error("Reflector encounter an event of ERROR")
                    return None, Exception()

                obj = e['object']
                if not isinstance(obj, self._watch_resouce_type):
                    LOG.error("Reflector expect type:%s, but watch event "
                              "object has type of %s",
                              self._watch_resouce_type, type(obj))
                    continue

                handle = self._event_handle.get(event_type)
                if not handle:
                    LOG.error("Reflector can not understand watch event:%s",
                              event_type)
                    continue

                handle(obj)
                new_resource_version = obj.metadata.resource_version

            return new_resource_version, None

        except Exception as ex:
            LOG.error('Reflector handle event failed, reason:%s', str(ex))
            return None, ex
