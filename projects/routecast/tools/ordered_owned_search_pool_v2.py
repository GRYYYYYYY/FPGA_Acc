"""Bounded requested-path batching; caller owns serial transaction commits.

One engine and single-thread executor per lane. Close each batch iterator even
when abandoning it. This adapter is caller-serial, not a concurrent public API.
"""
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait
from freeze_requested_search_result_v1 import freeze_requested


class SearchPool:
    def __init__(self, factory, workers=2, window=None):
        if not isinstance(workers, int) or workers < 1:
            raise ValueError('positive worker count required')
        self.window = workers if window is None else window
        if not isinstance(self.window, int) or self.window < 1:
            raise ValueError('positive pending window required')
        self.engines, self.executors = [], []
        self.active = self.closed = self.prepared = False
        try:
            for _ in range(workers):
                self.engines.append(factory())
                self.executors.append(ThreadPoolExecutor(max_workers=1))
        except BaseException:
            self.close()
            raise

    def prepare(self, prices, weight):
        if self.closed or self.active:
            raise RuntimeError('pool closed or batch active')
        self.prepared = False
        snapshot = dict(prices)
        for engine in self.engines:
            engine.prepare(snapshot, weight)
        self.prepared = True

    def search_many(self, queries):
        # Acquisition occurs on first iteration, so an unstarted iterator
        # cannot reserve a pool forever. Every started iterator needs close().
        if self.closed or self.active or not self.prepared:
            raise RuntimeError('pool unavailable or unprepared')
        self.active = True
        pending = deque()
        try:
            inputs = iter(queries)
            exhausted = False
            index = 0
            while pending or not exhausted:
                while not exhausted and len(pending) < self.window:
                    try:
                        source, targets = next(inputs)
                    except StopIteration:
                        exhausted = True
                        break
                    targets = frozenset(targets)
                    lane = index % len(self.engines)
                    index += 1
                    pending.append(self.executors[lane].submit(
                        self._search, self.engines[lane], source, targets))
                if pending:
                    answer = pending[0].result()
                    pending.popleft()
                    yield answer
        finally:
            for future in pending:
                future.cancel()
            wait(pending)
            self.active = False

    @staticmethod
    def _search(engine, source, targets):
        raw, parents, settled = engine.search(source, targets)
        return freeze_requested(source, targets, raw, parents, settled)

    def close(self):
        if self.active:
            raise RuntimeError('close active batch iterator first')
        if self.closed:
            return
        self.closed = True
        for executor in self.executors:
            executor.shutdown(wait=True, cancel_futures=True)
        for engine in self.engines:
            engine.close()
