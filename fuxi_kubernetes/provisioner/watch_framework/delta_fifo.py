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

from collections import defaultdict
from collections import namedtuple

from fuxi_kubernetes.common import constants


Delta = namedtuple('Delta', 'action, delta_object')


DeletedFinalStateUnknown = namedtuple('DeletedFinalStateUnknown', 'key, obj')


class DeltaFIFO(object):
    def __init__(self, key_func, known_objects):
        self._known_objects = known_objects
        self._key_func = key_func

        self._items = defaultdict(list)
        self._queue = []

    def add(self, resource):
        self._queue_action(constants.WATCH_EVENT_TYPE_ADDED, resource)

    def delete(self, resource):
        resource_id = self.keyof(resource)
        _, exists = self._known_objects.get_by_key(resource_id)
        if not exists and resource_id not in self._items:
            return

        self._queue_action(constants.WATCH_EVENT_TYPE_DELETED, resource)

    def update(self, resource):
        self._queue_action(constants.WATCH_EVENT_TYPE_MODIFIED, resource)

    def replace(self, resources, resource_version):
        keys = []
        for r in resources:
            keys.append(self.keyof(r))
            self._queue_action(constants.WATCH_EVENT_TYPE_SYNC, r)

        for k in self._known_objects.list_keys():
            if k in keys:
                continue
            deleted_obj, _ = self.known_objects.get_by_key(k)
            self._queue_action(constants.WATCH_EVENT_TYPE_DELETED,
                               DeletedFinalStateUnknown(k, deleted_obj))

    def pop(self):
        while self._queue:
            key = self._queue[0]
            if self._items.get(key):
                return key, self._items[key].pop(0)
            else:
                self._queue.pop(0)

        return None, None

    def keyof(self, resource):
        if isinstance(resource, DeletedFinalStateUnknown):
            return resource.key
        return self._key_func(resource)

    def _queue_action(self, action, resource):

        def _will_event_be_deleted(resource_id):
            deltas = self._items.get(resource_id)
            return deltas and (
                deltas[-1].action == constants.WATCH_EVENT_TYPE_DELETED)

        resource_id = self.keyof(resource)
        if action == constants.WATCH_EVENT_TYPE_SYNC and (
                _will_event_be_deleted(resource_id)):
            return

        if resource_id not in self._items:
            self._queue.append(resource_id)
        self._items[resource_id].append(Delta(action, resource))

        self._deduplicate_deltas(self._items[resource_id])

    def _deduplicate_deltas(self, deltas):

        def _filter_duplicate_deletion(item1, item2):
            if item1.action != constants.WATCH_EVENT_TYPE_DELETED or (
                    item2.action != constants.WATCH_EVENT_TYPE_DELETED):
                return None
            return item1 if isinstance(item2, DeletedFinalStateUnknown) else (
                item2)

        if len(deltas) < 2:
            return

        a = deltas[-1]
        b = deltas[-2]
        c = _filter_duplicate_deletion(a, b)
        if c:
            deltas.pop()
            deltas.pop()
            deltas.append(c)
