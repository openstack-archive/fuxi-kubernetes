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


class Cache(object):
    def __init__(self, key_func):
        self._key_func = key_func
        self._items = dict()

    def set_key_func(self, key_func):
        self._key_func = key_func

    def get_by_key(self, key):
        if key not in self._items:
            return None, False
        return self._items.get(key), True

    def list_keys(self):
        return self._items.iterkeys()

    def add(self, obj):
        self._items[self._key_func(obj)] = obj

    def delete(self, obj):
        self._items.pop(self._key_func(obj), None)

    def update(self, obj):
        self.add(obj)

    def get(self, obj):
        return self.get_by_key(self._key_func(obj))

    def replace(self, objs):
        self._items = {self._key_func(obj): obj for obj in objs}
