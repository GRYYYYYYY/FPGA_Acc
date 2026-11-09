"""Full compiled/Python A* result, retained-state and native-ticket parity."""
import json
import random
import resource
from collections import Counter
from fractions import Fraction
from pathlib import Path

from archive_design_exposure_v3 import sha
from verify_compiled_criticality_tree_v1 import graph
from static_quotient_lower_bound_v1 import LowerBound, Snapshot, Graph as PythonGraph
from compiled_quotient_adaptive128_v1_2026_10_18 import Graph as AdaptiveGraph,BINARY,BASE_BINARY
LANES=Counter()
class Graph(AdaptiveGraph):
    def close(self):
        if not getattr(self,'closed',True):
            LANES['fast128']+=self.fast_calls;LANES['fallback256']+=self.fallback_calls
        super().close()
from compiled_criticality_tree_v1 import NativePrices
from native_price_buffer_store_v1 import Store
from scaled_present_multiplicative_context_v1 import Context


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20))
    cases=retained=maximum_bits=0;statuses=Counter()
    for seed in range(200):
        rng=random.Random(seed);n=rng.randrange(3,32)
        fields,inc,initial=graph(rng,n,seed%2==0)
        count=rng.randrange(1,n+1)
        groups=list(range(count))+[rng.randrange(count) for _ in range(n-count)]
        floor=[rng.randrange(10)+(2**121 if seed%3==0 else 0) for _ in range(n)]
        lower=LowerBound(fields,inc,initial,floor,groups,max_targets=2)
        py=PythonGraph(lower);native=Graph(lower)
        try:
            for _ in range(4):
                source=rng.randrange(n);a=py.tree(source);b=native.tree(source)
                for k in range(6):
                    target=rng.randrange(n);c=[Fraction(0),Fraction(1),Fraction(2,3),Fraction(2**62-11,2**63-25)][k%4]
                    snapshot=Snapshot(lower,[v+rng.randrange(20)+(2**126 if seed%4==0 else 0) for v in floor])
                    budget=rng.randrange(10) if k%3==0 else 2**127
                    before=(dict(b.arrival),dict(b.parents));work=(py.settled,py.scanned,py.pushes)
                    x=a.expand(target,c,snapshot,budget);y=b.expand(target,c,snapshot,budget)
                    assert x==y,(seed,k,x,y)
                    assert a.arrival==b.arrival and a.parents==b.parents
                    assert native.last_stats[:3]==tuple(v-u for u,v in zip(work,(py.settled,py.scanned,py.pushes)))
                    if not y['committed']:assert before==(b.arrival,b.parents)
                    statuses[y['status']]+=1;cases+=1
                    maximum_bits=max(maximum_bits,y.get('objective_numerator',0).bit_length())
                # A directly imported valid retained shared tree is also supported.
                d=native.tree(source);d.arrival=dict(a.arrival);d.parents=dict(a.parents)
                snapshot=Snapshot(lower,floor);target=rng.randrange(n)
                assert d.expand(target,Fraction(2,3),snapshot,2**127)==a.expand(target,Fraction(2,3),snapshot,2**127)
                assert d.arrival==a.arrival and d.parents==a.parents;retained+=1
        finally:native.close()
    n=8;rows=[0];dest=[];inc=[]
    for u in range(n):
        for v in range(n):
            if u!=v:dest.append(v);inc.append(1+(u+v)%5)
        rows.append(len(dest))
    fields=dict(row_offsets=rows,dest_ranks=dest,capacities=[2]*n)
    base=tuple((i+1)*(2**90+3) for i in range(n));spans={i:i%3 for i in range(n)}
    floor=[base[i]+3*spans[i] for i in range(n)]
    lower=LowerBound(fields,inc,[0]*n,floor,list(range(n)))
    py=PythonGraph(lower);native=Graph(lower);store=Store(fields,base)
    context=Context(store,fields['capacities'],base,10,spans,4)
    native_cases=0;stale_rejected=0
    try:
        a=py.tree(0);b=native.tree(0)
        for epoch in range(5):
            history={i:spans[i]+epoch for i in range(n)}
            context.start_round(history,3,{i:1+i%3 for i in range(n)})
            for target in range(n):
                view=context.begin({0,1});prices=NativePrices(base,view)
                snapshot=Snapshot(lower,[prices.get(i) for i in range(n)])
                assert a.expand(target,Fraction(2,3),snapshot,2**127)==b.expand(target,Fraction(2,3),prices,2**127)
                assert a.arrival==b.arrival and a.parents==b.parents;native_cases+=1
                context.finish();before=dict(b.arrival),dict(b.parents)
                try:b.expand(0,Fraction(0),prices,0)
                except RuntimeError:stale_rejected+=1
                else:raise AssertionError('stale no-edge target accepted')
                assert before==(b.arrival,b.parents)
        context.start_round(spans,4,{i:1 for i in range(n)});view=context.begin({0});prices=NativePrices(base,view)
        before=dict(b.arrival),dict(b.parents)
        try:b.expand(0,Fraction(0),prices,0)
        except ValueError:pass
        else:raise AssertionError('changed static floor weight accepted')
        assert before==(b.arrival,b.parents);context.finish()
    finally:store.close();native.close()
    # Huge unused price potentials must not overflow the raw-only128 lane.
    fields=dict(row_offsets=list(range(8))+[7],dest_ranks=list(range(1,8)),capacities=[1]*8)
    lower=LowerBound(fields,[1]*7,[0]*8,[2**127-1]*8,list(range(8)))
    native=Graph(lower);py=PythonGraph(lower)
    try:
        snap=Snapshot(lower,lower.floor);a=py.tree(0);b=native.tree(0)
        assert a.expand(7,Fraction(1),snap,2**127)==b.expand(7,Fraction(1),snap,2**127)
        assert native.fast_calls==1 and native.table(7).maxfloor>=2**128
        # Conservative valid envelopes on both sides of the exact dispatch fence.
        h=native.table(7).maxraw
        for expected,envelope in [(True,2**127-1),(False,2**127)]:
            native.raw_bound=envelope-h;old=native.fast_calls
            assert py.tree(0).expand(7,Fraction(1),snap,2**127)==native.tree(0).expand(7,Fraction(1),snap,2**127)
            assert (native.fast_calls>old)==expected
    finally:native.close()
    native=Graph(lower);native.fast_unavailable=True
    try:
        assert native.tree(0).expand(7,Fraction(1),Snapshot(lower,lower.floor),2**127)==py.tree(0).expand(7,Fraction(1),Snapshot(lower,lower.floor),2**127)
        assert native.fast_calls==0 and native.fallback_calls==1
    finally:native.close()
    assert LANES['fast128']>0 and LANES['fallback256']>0
    assert cases==4800 and retained==800 and maximum_bits>160 and native_cases==stale_rejected==40
    assert all(statuses[k] for k in ('COMMITTED','UNREACHABLE','RETAIN_RAW_BUDGET'))
    root=Path(__file__).resolve().parents[1];out=root/'experiments/quotient_adaptive128_contract_v1_2026-10-18';out.mkdir()
    files=[Path(__file__),BINARY,BASE_BINARY,root/'tools/compiled_quotient_adaptive128_v1_2026_10_18.py',root/'tools/soft_demand_cpp/quotient_adaptive128_v1_2026_10_18.cpp',root/'tools/compiled_quotient_criticality_astar_v1.py',
           root/'tools/static_quotient_lower_bound_v1.py',root/'tools/compiled_criticality_tree_v1.py',
           root/'tools/soft_demand_cpp/quotient_criticality_astar_v1.cpp',root/'tools/soft_demand_cpp/criticality_tree_exact_v2.cpp',
           root/'tools/scaled_present_multiplicative_context_v1.py',root/'tools/native_price_buffer_store_v1.py']
    value=dict(bindings={str(p):sha(p) for p in files},all_pass=True,lane_calls=dict(LANES),huge_unused_floor_potential_case_pass=True,exact127bit_dispatch_fence_cases_pass=True,disabled_fast_lane_fallback_pass=True,random_graphs=200,
        sequential_expansions=cases,retained_seed_continuations=retained,
        result_path_tree_and_work_counts_equal_python_Astar=True,maximum_objective_bits=maximum_bits,
        status_counts=dict(statuses),native_owner_excluded_snapshot_cases=native_cases,
        stale_already_owned_target_rejections=stale_rejected,changed_floor_weight_rejected=True,
        original_Dijkstra_tie_path_parity_claimed=False,
        scope='Adaptive checked128 plus original256 fallback primitive parity with independent Python A*. Both lane counts, huge unused potentials and dispatch fence validated. Current live model unchanged. Actual optimal weighted objectives preserved; old Dijkstra tied paths/budgets/whole-model trajectories may change. No full model, quality, paired/full-workflow or hardware gain claimed.')
    (out/'verification.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({k:v for k,v in value.items() if k!='bindings'}))


if __name__=='__main__':main()
