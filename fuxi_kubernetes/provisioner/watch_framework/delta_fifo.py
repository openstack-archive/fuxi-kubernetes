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


class _KnownObject(object):
    def __init__(self, key_func):
        self._key_func = key_func
        self._items = dict()

    def __contains__(self, item):
        return self._key_func(item) in self._items

    def __iter__(self):
        return self._items.iteritems()

    def add(self, item):
        self._items[self._key_func(item)] = item

    def delete(self, item):
        self._items.pop(self._key_func(item), None)

    def update(self, item):
        self.add(item)

    def get(self, item):
        return self._items.get(self._key_func(item), None)


class DeltaFIFO(object):
    def __init__(self, key_func):
        self._key_func = key_func
        self._known_objects = _KnownObject(self._keyof)
        self._items = defaultdict(list)
        self._queue = []

    def add(self, obj):
        self._queue_action(constants.WATCH_EVENT_TYPE_ADDED, obj)

    def delete(self, obj):
        if obj not in self._known_objects and (
                self._keyof(obj) not in self._items):
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
            keys.append(self._keyof(obj))
            self._queue_action(constants.WATCH_EVENT_TYPE_SYNC, obj)

        for k, obj in self._known_objects:
            if k not in keys:
                self._queue_action(constants.WATCH_EVENT_TYPE_DELETED,
                                   DeletedFinalStateUnknown(k, obj))

    def pop(self):

        def _convert(delta):
            add_update_events = [
                constants.WATCH_EVENT_TYPE_ADDED,
                constants.WATCH_EVENT_TYPE_MODIFIED,
                constants.WATCH_EVENT_TYPE_SYNC
            ]
            known_objects = self._known_objects

            action, obj = delta
            if action in add_update_events:
                if obj in known_objects:
                    old = known_objects.get(obj)
                    known_objects.update(obj)
                    return constants.WATCH_EVENT_TYPE_MODIFIED, (old, obj)
                else:
                    known_objects.add(obj)
                    return constants.WATCH_EVENT_TYPE_ADDED, (obj,)

            elif action == constants.WATCH_EVENT_TYPE_DELETED:
                known_objects.delete(obj)
                if not isinstance(obj, DeletedFinalStateUnknown):
                    return action, (obj,)

            return None, None

        while self._queue:
            key = self._queue[0]
            if self._items.get(key):
                event, obj = _convert(self._items[key].pop(0))
                if event:
                    return event, obj
            else:
                self._queue.pop(0)
                self._items.pop(key, None)

        return None, None

    def _keyof(self, obj):
        return obj.key if isinstance(
            obj, DeletedFinalStateUnknown) else self._key_func(obj)

    def _queue_action(self, action, obj):

        def _will_event_be_deleted(obj_key):
            deltas = self._items.get(obj_key)
            return deltas and (
                deltas[-1].action == constants.WATCH_EVENT_TYPE_DELETED)

        obj_key = self._keyof(obj)
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
