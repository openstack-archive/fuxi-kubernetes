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

from fuxi_kubernetes.common import constants


ResouceEventHandler = namedtuple('ResouceEventHandler',
                                 'on_add, on_delete, on_update')


class Consumer(object):
    def __init__(self, store, event_handler):
        self._store = store
        self._resource_event_handler = {
            constants.WATCH_EVENT_TYPE_ADDED: event_handler.on_add,
            constants.WATCH_EVENT_TYPE_MODIFIED: event_handler.on_update,
            constants.WATCH_EVENT_TYPE_DELETED: event_handler.on_delete
        }
        self._running = False

    def stop(self):
        self._running = False

    def start(self):

        def _f():
            while self._running:
                action, resource = self._store.pop()
                if not action:
                    # If no event happens, wait for a while.
                    eventlet.sleep(1)
                    continue

                self._resource_event_handler[action](*resource)

                # Cooperate with other green thread
                eventlet.sleep(0)

        self._running = True
        eventlet.spawn(_f)
