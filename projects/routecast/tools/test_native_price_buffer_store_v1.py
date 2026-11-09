"""Exact owner-set/epoch oracle and compiled price borrowing on actual Context."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import random
import sys

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from native_price_buffer_store_v1 import Store
from cached_multiplicative_occupancy_context_v1 import Context
from compiled_criticality_tree_v1 import Graph,NativePrices,BINARY
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference


def rejects(fn,kind):
    try:fn()
    except kind:return
    raise AssertionError('invalid operation admitted')


def main():
    rng=random.Random(20261015);transactions=queries=expansions=0
    for trial in range(100):
        n=12;m=8;caps=tuple(rng.randrange(1,4) for _ in range(n))
        base=tuple(rng.randrange(1000)+(2**65 if trial%2 else 0) for _ in range(n))
        span={i:rng.randrange(5) for i in range(n)};owners=[{j for j in range(m) if rng.randrange(3)==0} for _ in range(n)]
        store=Store(dict(capacities=caps),base);context=Context(store,caps,base,m,span)
        rows=list(range(n+1));rows[-1]=n-1;dest=list(range(1,n));inc=[i+1 for i in range(n-1)]
        graph=Graph(dict(row_offsets=rows,dest_ranks=dest),inc,[0]*n)
        reference=Reference(dict(row_offsets=rows,dest_ranks=dest),inc,[0]*n)
        previous=None
        try:
            for round_ in range(3):
                history=[rng.randrange(6) for _ in range(n)];weight=rng.randrange(8)
                context.start_round({i:history[i]+span[i] for i in range(n)},weight,{i:len(x) for i,x in enumerate(owners)})
                for step in range(10):
                    net=rng.randrange(m);old={i for i,x in enumerate(owners) if net in x};view=context.begin(old)
                    prices=NativePrices(base,view)
                    if previous is not None:rejects(lambda:previous.get(0),RuntimeError)
                    for i in range(n):
                        occupancy=len(owners[i]-{net});present=1+max(0,occupancy-caps[i]+1)
                        expected=base[i]*(1+history[i])*present+weight*span[i]
                        assert view.get(i)==store.prices[i]==store.backends[1].forward.price[i]==expected-base[i]
                        assert prices.get(i)==expected;queries+=1
                    target=rng.randrange(n)
                    assert graph.tree(0).expand(target,Fraction(3,7),prices,2**127)==reference.tree(0).expand(target,Fraction(3,7),prices,2**127)
                    expansions+=1
                    new={i for i in range(n) if rng.randrange(3)==0}
                    for i in old-new:owners[i].remove(net)
                    for i in new-old:owners[i].add(net)
                    context.finish({i:len(owners[i]) for i in old^new})
                    rejects(lambda:prices.buffers(graph),RuntimeError)
                    previous=prices;transactions+=1
                    for i in range(n):
                        assert context.ledger.get(i,0)==len(owners[i])
                        assert store.prices[i]==store.backends[1].forward.price[i]==context.price(i,len(owners[i]))
            original=list(store.prices)
            for patch in [{0:0,n:1},{True:1},{0:-1},{0:store.price_ceiling+1}]:
                rejects(lambda:store.patch_prices(patch),ValueError)
                assert store.prices==original and [store.backends[1].forward.price[i] for i in range(n)]==original
            store.close();rejects(lambda:store.patch_prices({0:0}),RuntimeError)
        finally:graph.close()
    # Values that do not fit the old optimization envelope remain exact price
    # values. This store never authorizes a legacy narrow path search.
    s=Store(dict(capacities=[1]),(0,));s.prepare({0:2**126},1,price_ceiling=2**127)
    assert s.backends[1].forward.price[0]==2**126
    rejects(lambda:s.prepare({0:2**128},1,price_ceiling=2**127),ValueError)
    assert s.prices==[2**126];s.close()
    output=R/'experiments/native_price_buffer_store_contract_v1_2026-10-15';output.mkdir(exist_ok=False)
    result=dict(bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY)},all_pass=True,
        original_Context_transactions=transactions,independent_owner_set_node_prices=queries,
        compiled_borrowed_price_expansions_exact_reference_equal=expansions,
        all_sparse_patches_python_and_native_buffers_equal=True,stale_snapshot_and_invalid_patch_guards_pass=True,
        exact_price_values_above_120_bits_pass=True,
        scope='Actual unchanged Context plus price-only Store, independent owner-set formula, compiled-vs-reference expansions. Full design states/events and resident savings remain separate.')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)


if __name__=='__main__':main()
