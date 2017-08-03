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
    def __init__(self, cache, fifo, resource_event_handler):
        self._cache = cache
        self._fifo = fifo
        self._resource_event_handler = resource_event_handler
        self._running = False

    def stop(self):
        self._running = False

    def start(self):
        def _f():
            while self._running:
                _, resource_event = self._fifo.pop()
                if not resource_event:
                    eventlet.sleep(1)
                    continue

                self._process_resource_event(resource_event)

        self._running = True
        eventlet.spawn(_f)

    def _process_resource_event(self, resource_event):
        add_update_events = [
            constants.WATCH_EVENT_TYPE_ADDED,
            constants.WATCH_EVENT_TYPE_MODIFIED,
            constants.WATCH_EVENT_TYPE_SYNC
        ]

        handler = self._resource_event_handler
        cache = self._cache
        action, resource = resource_event
        if action in add_update_events:
            old, exists = cache.get(resource)
            if exists:
                cache.update(resource)
                handler.on_update(old, resource)
            else:
                cache.add(resource)
                handler.on_add(resource)
        elif action == constants.WATCH_EVENT_TYPE_DELETED:
            cache.delete(resource)
            handler.on_delete(resource)
