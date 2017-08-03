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
from oslo_log import log as logging

from fuxi_kubernetes.common import constants

LOG = logging.getLogger(__name__)


Delta = namedtuple('Delta', 'action, delta_object')


DeletedFinalStateUnknown = namedtuple('DeletedFinalStateUnknown', 'key, obj')


class DeltaFIFO(object):
    def __init__(self, key_func, known_objects):
        self._known_objects = known_objects
        self._key_func = key_func

        self._items = defaultdict(list)
        self._queue = []

    def add(self, obj):
        self._queue_action(constants.WATCH_EVENT_TYPE_ADDED, obj)

    def delete(self, obj):
        obj_key = self.keyof(obj)
        _, exists = self._known_objects.get_by_key(obj_key)
        if not exists and obj_key not in self._items:
            LOG.warn("DeltaFIFO ignore deleting obj with type of: (%s). "
                     "Because this obj is both not in fifo and known objects",
                     type(obj))
            return

        self._queue_action(constants.WATCH_EVENT_TYPE_DELETED, obj)

    def update(self, obj):
        self._queue_action(constants.WATCH_EVENT_TYPE_MODIFIED, obj)

    def replace(self, objs):
        keys = []
        for obj in objs:
            keys.append(self.keyof(obj))
            self._queue_action(constants.WATCH_EVENT_TYPE_SYNC, obj)

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
                self._items.pop(key, None)

        return None, None

    def keyof(self, obj):
        if isinstance(obj, DeletedFinalStateUnknown):
            return obj.key
        return self._key_func(obj)

    def _queue_action(self, action, obj):

        def _will_event_be_deleted(obj_key):
            deltas = self._items.get(obj_key)
            return deltas and (
                deltas[-1].action == constants.WATCH_EVENT_TYPE_DELETED)

        obj_key = self.keyof(obj)
        if action == constants.WATCH_EVENT_TYPE_SYNC and (
                _will_event_be_deleted(obj_key)):
            return

        if obj_key not in self._items:
            self._queue.append(obj_key)
        self._items[obj_key].append(Delta(action, obj))

        self._deduplicate_deltas(self._items[obj_key])

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
