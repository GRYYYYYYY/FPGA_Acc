"""Real context transaction and integer price equivalence with independent formula."""
import random
from collections import Counter
from cached_multiplicative_occupancy_context_v1 import Context as Original
from factored_multiplicative_context_v1 import Context as Factored


class Search:
    def __init__(self, caps, base):
        self.fields={'capacities':tuple(caps)};self.base=tuple(base);self.closed=False
    def prepare(self, prices, *args, **kwargs):self.prices=dict(prices)
    def patch_prices(self, prices):self.prices.update(prices)


def main():
    rng=random.Random(20261020);checks=0
    for _ in range(100):
        caps=[rng.randrange(4) for _ in range(31)];base=[rng.randrange(1<<60) for _ in caps]
        spans={n:rng.randrange(8) for n in range(len(caps))};history={n:spans[n]+rng.randrange(1<<30) for n in spans};weight=rng.randrange(1<<40)
        ledger=Counter({n:rng.randrange(1,8) for n,c in enumerate(caps) if c})
        contexts=[C(Search(caps,base),caps,base,8,spans) for C in [Original,Factored]]
        for c in contexts:c.start_round(history,weight,ledger)
        assert contexts[0].search.prices==contexts[1].search.prices
        for _ in range(20):
            old={n for n in ledger if rng.randrange(2)};views=[c.begin(old) for c in contexts]
            for node in range(len(caps)):
                other=ledger.get(node,0)-(node in old);expected=base[node]*(1+history[node]-spans[node])*(1+max(0,other-caps[node]+1))+weight*spans[node]-base[node]
                assert views[0].get(node)==views[1].get(node)==expected;checks+=1
            updates={}
            for node,cap in enumerate(caps):
                if not cap or rng.randrange(4):continue
                count=ledger.get(node,0)
                if node in old:updates[node]=count-1
                elif count<8:updates[node]=count+1
            for c in contexts:c.finish(updates)
            assert contexts[0].search.prices==contexts[1].search.prices
            assert contexts[0].ledger==contexts[1].ledger
            for node,count in updates.items():
                if count:ledger[node]=count
                else:ledger.pop(node,None)
            for view in views:
                try:view.get(0)
                except RuntimeError:pass
                else:raise AssertionError('stale view accepted')
    print('FACTORED_CONTEXT_EXACT_TRANSACTION_PRICE_CHECKS',checks)


if __name__=='__main__':main()
