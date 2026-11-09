"""Process-local complete-NET initial search reuse; feedback always freshly searched."""
from collections import Counter, OrderedDict
from copy import deepcopy
from hybrid_bidirectional_search_v1 import Search as Original
_CACHE = OrderedDict()
_LIMITS = dict(groups=4096, parents=262144, queries=16384)
_USAGE = Counter()
def _remove(key):
    value = _CACHE.pop(key)
    _USAGE['parents'] -= len(value[1])
    _USAGE['queries'] -= len(key[1])

def reset():
    _CACHE.clear(); _STATS.clear(); _USAGE.clear()
_STATS = Counter()
class Search(Original):
    def configure_initial_groups(self, digest, queries, bindings):
        self.identity = (digest, self.rc.scale, tuple(sorted(bindings.items())))
        # Endpoint hashes vary by layout and are deliberately outside static identity.
        self.groups = {}
        for q in queries:
            self.groups.setdefault(q['net_id'], []).append(tuple(sorted(q.items())))
        self.group_keys = {}
        for net, group in sorted(self.groups.items()):
            rows = [dict(q) for q in group]
            key = (rows[0]['source'], frozenset(q['sink'] for q in rows))
            self.group_keys.setdefault(key, []).append(tuple(group))
        live = {(self.identity, tuple(group)) for group in self.groups.values()}
        for key in list(_CACHE):
            if key not in live:
                _remove(key); _STATS['invalidated_groups'] += 1
        self.zero = True
    def prepare(self, prices, weight):
        super().prepare(prices, weight)
        self.zero = not prices and weight == 0
    def search(self, source, sinks):
        targets = frozenset(sinks)
        if not self.zero or not hasattr(self, 'identity'):
            return super().search(source, targets)
        groups = self.group_keys[(source, targets)]
        group = groups.pop(0)
        key = (self.identity, group)
        if key in _CACHE:
            _STATS['hits'] += 1
            _CACHE.move_to_end(key)
            return deepcopy(_CACHE[key])
        _STATS['misses'] += 1
        d, parents, settled = super().search(source, targets)
        if not targets.issubset(settled):
            return d, parents, settled
        # Initial consumer traverses only requested paths; retain every such parent.
        kept = {}
        for sink in targets:
            u = sink
            while u != source:
                previous, slot = parents[u]
                kept[u] = (previous, slot)
                u = previous
        value = ({t:d[t] for t in targets}, kept, set(targets))
        if len(kept) > _LIMITS['parents'] or len(group) > _LIMITS['queries']:
            _STATS['oversize_uncached'] += 1
            return value
        while _CACHE and (len(_CACHE) >= _LIMITS['groups'] or
                _USAGE['parents'] + len(kept) > _LIMITS['parents'] or
                _USAGE['queries'] + len(group) > _LIMITS['queries']):
            _remove(next(iter(_CACHE))); _STATS['capacity_evictions'] += 1
        _CACHE[key] = deepcopy(value)
        _USAGE['parents'] += len(kept); _USAGE['queries'] += len(group)
        return value

def diagnostics():
    return dict(_STATS, cached_groups=len(_CACHE), retained_parent_slots=_USAGE['parents'], retained_query_records=_USAGE['queries'], limits=dict(_LIMITS))
