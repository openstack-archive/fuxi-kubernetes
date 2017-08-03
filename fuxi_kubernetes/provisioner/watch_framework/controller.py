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

from fuxi_kubernetes.provisioner.watch_framework import cache as store_cache
from fuxi_kubernetes.provisioner.watch_framework import consumer
from fuxi_kubernetes.provisioner.watch_framework import delta_fifo
from fuxi_kubernetes.provisioner.watch_framework import producer


class Controller(object):
    def __init__(self, resource_type, key_func, lw, watch_timeout,
                 resource_event_handler):
        self._cache = store_cache.Cache(None)
        self._fifo = delta_fifo.DeltaFIFO(key_func, self._cache)
        self._cache.set_key_func(self._fifo.keyof)

        self._producer = producer.Producer(
            resource_type, lw, watch_timeout, self._fifo)

        self._consumer = consumer.Consumer(
            self._cache, self._fifo, resource_event_handler)

    def start(self):
        self._producer.start()
        self._consumer.start()

    def stop(self):
        self._producer.stop()
        self._consumer.stop()
