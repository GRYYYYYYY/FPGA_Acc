"""Local atomic ledger; explicit arc paths, not VPR route-tree legality.

Batch validation touches submitted paths and affected net/source counters only.
Full snapshots, fork, occupancy export and rebuild remain explicit O(state) work.
"""
from collections import Counter
from collections.abc import Mapping
from connection_golden import Result, UINT64_MAX, integer
from rr_occupancy import Occupancy


class LocalBatchOccupancy(Occupancy):
    def __init__(self, graph):
        super().__init__(graph)
        self._roots = {}

    def fork(self):
        branch = LocalBatchOccupancy(self.graph)
        branch._states = dict(self._states)
        branch._refs = self._refs.copy()
        branch._occupancy = self._occupancy.copy()
        branch._roots = {net: counts.copy() for net, counts in self._roots.items()}
        return branch

    def update(self, connection_id, epoch, net_id=None, source=None, sink=None,
               edge_ids=None, *, remove=False):
        row = dict(connection_id=connection_id, epoch=epoch, remove=remove)
        if not remove or any(x is not None for x in (net_id, source, sink, edge_ids)):
            row.update(net_id=net_id, source=source, sink=sink, edge_ids=edge_ids)
        return self.update_batch([row])

    def update_batch(self, updates):
        if not isinstance(updates, (list, tuple)) or not updates:
            return Result.INVALID
        seen = set()
        staged = []
        roots = {}
        delta = Counter()
        prepared = []
        for row in updates:
            if not isinstance(row, Mapping) or set(row) - {
                'connection_id', 'epoch', 'net_id', 'source', 'sink', 'edge_ids', 'remove'
            }:
                return Result.INVALID
            cid, epoch = row.get('connection_id'), row.get('epoch')
            remove = row.get('remove', False)
            if (not integer(cid, 0, UINT64_MAX) or not integer(epoch, 1, UINT64_MAX)
                    or type(remove) is not bool or cid in seen):
                return Result.INVALID
            seen.add(cid)
            old = self._states.get(cid)
            if old is not None and epoch <= old[0]:
                return Result.STALE
            prepared.append((dict(row), old))
        # Match reference precedence: batch identity/epoch checks precede paths.
        for row, old in prepared:
            cid, epoch = row['connection_id'], row['epoch']
            # Reuse independent single-path checks on an empty temporary ledger.
            validator = Occupancy(self.graph)
            if validator.update(**row) != Result.COMMITTED:
                return Result.INVALID
            replacement = validator._states[cid][1]
            staged.append((cid, epoch, replacement))
            for conn, sign in ((old[1] if old else None, -1), (replacement, 1)):
                if conn is None:
                    continue
                if conn.net_id not in roots:
                    roots[conn.net_id] = self._roots.get(conn.net_id, Counter()).copy()
                roots[conn.net_id][conn.source] += sign
                for nid in conn.nodes:
                    delta[(conn.net_id, nid)] += sign
        for net, counts in roots.items():
            if any(value < 0 for value in counts.values()):
                raise AssertionError('source reference underflow')
            roots[net] = Counter({source: value for source, value in counts.items() if value})
            if len(roots[net]) > 1:
                return Result.INVALID
        # Validate every delta before publishing any state.
        for key, value in delta.items():
            if self._refs[key] + value < 0:
                raise AssertionError('node reference underflow')
        for key, value in delta.items():
            old_count = self._refs[key]
            new_count = old_count + value
            self._occupancy[key[1]] += int(new_count > 0) - int(old_count > 0)
            if new_count:
                self._refs[key] = new_count
            else:
                self._refs.pop(key, None)
        for net, counts in roots.items():
            if counts:
                self._roots[net] = counts
            else:
                self._roots.pop(net, None)
        for cid, epoch, conn in staged:
            self._states[cid] = (epoch, conn)
        return Result.COMMITTED
