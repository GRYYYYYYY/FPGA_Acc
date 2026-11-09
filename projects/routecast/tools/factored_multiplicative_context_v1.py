"""Exact per-round factoring; same owner-release and cached snapshot mechanics."""
from cached_multiplicative_occupancy_context_v1 import Context as OriginalContext


class Context(OriginalContext):
    def start_round(self, history, weight, ledger):
        if self.active is not None:
            raise RuntimeError('active transaction at round change')
        if type(weight) is not int or not 0 <= weight < 2**64:
            raise ValueError('weight')
        h = tuple(history.get(n, 0)-self.spans[n] for n in range(len(self.caps)))
        if any(type(v) is not int or v < 0 for v in h):
            raise ValueError('history missing static span or invalid count')
        if any(type(v) is not int or v < 0 for v in self.base):
            raise ValueError('base domain')
        self._history_base = tuple(b*(1+a) for b,a in zip(self.base,h))
        self._static_price = tuple(weight*s-b for s,b in zip(self.spans,self.base))
        return super().start_round(history, weight, ledger)

    def price(self, node, count):
        if type(count) is not int or count < 0 or count and self.caps[node] == 0:
            raise ValueError('occupancy domain')
        excess = count-self.caps[node]+1
        return self._history_base[node]*(1+(excess if excess > 0 else 0))+self._static_price[node]
