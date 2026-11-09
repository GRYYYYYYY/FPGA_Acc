"""Instrument unchanged public hybrid searches; never retain borrowed results."""
from collections import defaultdict
from time import perf_counter
from hybrid_bidirectional_search_v1 import Search as Original

rows = defaultdict(lambda: dict(calls=0, requested_sinks=0, seconds=0.0))

class Search(Original):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phase = -1

    def prepare(self, prices, weight):
        result = super().prepare(prices, weight)
        self.phase += 1
        return result

    def search(self, source, sinks):
        targets = set(sinks)
        key = (self.phase, len(targets))
        start = perf_counter()
        result = super().search(source, targets)
        seconds = perf_counter() - start
        row = rows[key]
        row['calls'] += 1
        row['requested_sinks'] += len(targets)
        row['seconds'] += seconds
        return result

def snapshot():
    return [dict(phase=phase, unique_sinks=sinks,
                 engine='bidirectional' if sinks == 1 else 'forward', **values)
            for (phase, sinks), values in sorted(rows.items())]
