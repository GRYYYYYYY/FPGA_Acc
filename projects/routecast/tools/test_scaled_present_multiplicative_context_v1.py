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
from scaled_present_multiplicative_context_v1 import Context
from multiplicative_net_congestion_v1 import cost as baseline_cost
from compiled_criticality_tree_v1 import Graph,NativePrices,BINARY
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference


def rejects(fn,kind):
    try:fn()
    except kind:return
    raise AssertionError('invalid operation admitted')


def main():
    rng=random.Random(20261015);transactions=queries=expansions=0
    for trial in range(300):
        factor=(1,2,4)[trial%3]
        n=12;m=8;caps=tuple(rng.randrange(1,4) for _ in range(n))
        base=tuple(rng.randrange(1000)+(2**65 if trial%2 else 0) for _ in range(n))
        span={i:rng.randrange(5) for i in range(n)};owners=[{j for j in range(m) if rng.randrange(3)==0} for _ in range(n)]
        store=Store(dict(capacities=caps),base);context=Context(store,caps,base,m,span,factor)
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
                        occupancy=len(owners[i]-{net});present=1+factor*max(0,occupancy-caps[i]+1)
                        expected=base[i]*(1+history[i])*present+weight*span[i]
                        assert view.get(i)==store.prices[i]==store.backends[1].forward.price[i]==expected-base[i]
                        assert prices.get(i)==expected;queries+=1
                        if factor==1:assert expected==baseline_cost(base[i],history[i],occupancy,caps[i],False,weight*span[i])
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
            old_round=(context.history,context.weight,dict(context.ledger),list(store.prices))
            rejects(lambda:context.start_round({i:span[i]+2**128 for i in range(n)},1,context.ledger),ValueError)
            assert old_round==(context.history,context.weight,dict(context.ledger),list(store.prices))
            rejects(lambda:Context(store,caps,base,m,span,True),ValueError)
            rejects(lambda:Context(store,caps,base,m,span,3),ValueError)
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
    output=R/'experiments/scaled_present_price_contract_v1_2026-10-15';output.mkdir(exist_ok=False)
    result=dict(bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY)},all_pass=True,
        scaled_Context_transactions=transactions, factors=[1,2,4], factor1_original_formula_equal=True, failed_round_prepare_preserves_previous_state=True,independent_owner_set_node_prices=queries,
        compiled_borrowed_price_expansions_exact_reference_equal=expansions,
        all_sparse_patches_python_and_native_buffers_equal=True,stale_snapshot_and_invalid_patch_guards_pass=True,
        exact_price_values_above_120_bits_pass=True,
        scope='Isolated scaled-present Context with exact owner-set polynomial oracle and compiled-vs-reference expansions. Original model unchanged. No full-design audit, routing quality, heldout or memory-saving proof.')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)


if __name__=='__main__':main()
