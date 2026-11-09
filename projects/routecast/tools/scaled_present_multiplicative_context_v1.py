"""Development-only present-factor ablation; no live model imports this module."""
from collections import Counter
from cached_multiplicative_occupancy_context_v1 import Context as Baseline


class Context(Baseline):
    def __init__(self, search, capacities, node_base, max_owners, span_prices, present_factor):
        if type(present_factor) is not int or present_factor not in (1, 2, 4):
            raise ValueError('preregistered integer present factor required')
        super().__init__(search, capacities, node_base, max_owners, span_prices)
        self.present_factor = present_factor

    def price(self, node, count):
        self.check_count(node, count)
        over = max(0, count - self.caps[node] + 1)
        return (self.base[node] * (1 + self.history[node])
                * (1 + self.present_factor * over)
                + self.weight * self.spans[node] - self.base[node])

    def start_round(self, history, weight, ledger):
        if self.active is not None:
            raise RuntimeError('active transaction at round change')
        if type(weight) is not int or not 0 <= weight < 2**64:
            raise ValueError('weight')
        h = tuple(history.get(n, 0) - self.spans[n] for n in range(len(self.caps)))
        if any(type(v) is not int or v < 0 for v in h):
            raise ValueError('invalid history')
        counts = dict(ledger)
        for n, v in counts.items():
            self.check_count(n, v)
        # Compute/validate before publishing a new round. Store.prepare itself
        # validates and allocates before replacing its previous price buffer.
        ceiling = (max(self.base, default=0) * (1 + max(h, default=0))
                   * (1 + self.present_factor * (self.limit + 1))
                   + weight * max(self.spans, default=0))
        prices = {
            n: self.base[n] * (1 + h[n])
            * (1 + self.present_factor * max(0, counts.get(n, 0) - self.caps[n] + 1))
            + weight * self.spans[n] - self.base[n]
            for n in range(len(h))
        }
        self.search.prepare(prices, 1, structural=True, price_ceiling=ceiling)
        self.history = h
        self.weight = weight
        self.ledger = Counter({n: v for n, v in counts.items() if v})
        self.ready = True
