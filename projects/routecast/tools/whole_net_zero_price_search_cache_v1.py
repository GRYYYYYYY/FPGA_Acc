"""Process-local complete-NET initial search reuse; feedback always freshly searched."""
from collections import Counter
from copy import deepcopy
from hybrid_bidirectional_search_v1 import Search as Original
_CACHE = {}
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
        _CACHE[key] = deepcopy(value)
        return value

def diagnostics():
    return dict(_STATS, cached_groups=len(_CACHE))
