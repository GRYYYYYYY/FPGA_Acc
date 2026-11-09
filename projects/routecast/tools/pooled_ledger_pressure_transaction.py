"""Single publication of validated occupancy and pressure, with full-state staging.

The graph and metadata are caller-authenticated immutable inputs. Fork/copy cost
is O(active state), deliberately explicit; this is not a local-cost optimization.
"""
from threading import RLock
from collections.abc import Mapping
from connection_golden import Result
from rr_local_batch_occupancy import LocalBatchOccupancy
from incremental_pooled_pressure import PooledPressure


class PooledLedgerPressureTransaction:
    def __init__(self, graph, fields, graph_sha256):
        ledger = LocalBatchOccupancy(graph)
        cache = PooledPressure(fields)
        payload = cache.payload(graph_sha256)
        self._graph_sha256 = graph_sha256
        self._current = (ledger, cache, payload)
        self._lock = RLock()

    def snapshot(self):
        """Detached values captured from one jointly published state."""
        with self._lock:
            ledger, cache, payload = self._current
            return {'states': ledger.states,
                    'occupancy': {n: v for n, v in ledger._occupancy.items() if v},
                    'pressure_rows': dict(cache.rows), 'payload': payload}

    def update_batch(self, updates):
        with self._lock:
            if not isinstance(updates, (list, tuple)) or not updates:
                return Result.INVALID
            # Validation and dirty derivation must use the same request values.
            # The lock owns our state, not the caller's mutable list/dicts/paths.
            requests = []
            for row in updates:
                if not isinstance(row, Mapping):
                    return Result.INVALID
                copied = dict(row)
                path = copied.get('edge_ids')
                if isinstance(path, (list, tuple)):
                    copied['edge_ids'] = tuple(path)
                requests.append(copied)
            ledger, cache, _ = self._current
            staged = ledger.fork()
            status = staged.update_batch(requests)
            if status != Result.COMMITTED:
                return status
            dirty = set()
            for row in requests:
                cid = row['connection_id']
                for state in (ledger._states.get(cid), staged._states.get(cid)):
                    if state is not None and state[1] is not None:
                        dirty.update(state[1].nodes)
            pressure = cache.fork()
            pressure.refresh(staged._occupancy, dirty)
            payload = pressure.payload(self._graph_sha256)
            # Readers under the same lock cannot observe a partially published pair.
            self._current = (staged, pressure, payload)
            return Result.COMMITTED
