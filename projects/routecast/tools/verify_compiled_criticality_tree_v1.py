"""Complete result/path/tree parity against arbitrary-integer reference search."""
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
from compiled_criticality_tree_v1 import Graph as Compiled, BINARY
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from criticality_retained_net_primary_v1 import route


def graph(rng,n,wide):
    rows=[0];dest=[];inc=[]
    for u in range(n):
        for v in range(n):
            if rng.random()<.13:
                for _ in range(1+(rng.random()<.08)):
                    dest.append(v);inc.append(rng.randrange(12)+(2**110 if wide and rng.random()<.4 else 0))
        rows.append(len(dest))
    return dict(row_offsets=rows,dest_ranks=dest),inc,[rng.randrange(4) for _ in range(n)]


def main():
    results=Counter();maximum_bits=0;net_cases=0;seeded_cases=0
    for seed in range(200):
        rng=random.Random(seed);n=rng.randrange(3,32);f,inc,initial=graph(rng,n,seed%2==0)
        native=Compiled(f,inc,initial);reference=Reference(f,inc,initial)
        try:
            for tree_index in range(4):
                source=rng.randrange(n);a=reference.tree(source);b=native.tree(source)
                for query_index in range(6):
                    target=rng.randrange(n)
                    criticality=[Fraction(0),Fraction(1),Fraction(1,2),Fraction(2**62-11,2**63-25)][query_index%4]
                    prices={i:rng.randrange(20)+(2**126 if seed%3==0 and i%2 else 0) for i in range(n)}
                    budget=2**127 if query_index%3 else rng.randrange(10)
                    before=(dict(b.arrival),dict(b.parents))
                    x=a.expand(target,criticality,prices,budget);y=b.expand(target,criticality,prices,budget)
                    assert x==y,(seed,tree_index,query_index,x,y)
                    assert a.arrival==b.arrival and a.parents==b.parents
                    if not y['committed']:assert before==(b.arrival,b.parents)
                    results[y['status']]+=1
                    maximum_bits=max(maximum_bits,y.get('objective_numerator',0).bit_length())
                # Direct retained-tree import of an already validated tree;
                # subsequent expansion must preserve all shared attach paths.
                c=native.tree(source);c.arrival=dict(a.arrival);c.parents=dict(a.parents)
                target=rng.randrange(n);prices={i:rng.randrange(30) for i in range(n)}
                assert c.expand(target,Fraction(3,5),prices,2**127)==a.expand(target,Fraction(3,5),prices,2**127)
                assert c.arrival==a.arrival and c.parents==a.parents
                seeded_cases+=1
        finally:native.close()
    for seed in range(100):
        rng=random.Random(1000+seed);n=24
        # Always reachable chain plus forward shortcuts/parallel ties, so old
        # paths are valid and share one consistent source-rooted tree.
        rows=[0];dest=[];inc=[]
        for u in range(n):
            if u+1<n:dest.append(u+1);inc.append(1+seed%3)
            for v in range(u+2,n):
                if rng.random()<.07:dest.append(v);inc.append(rng.randrange(8))
            rows.append(len(dest))
        f=dict(row_offsets=rows,dest_ranks=dest);reference=Reference(f,inc,[0]*n);native=Compiled(f,inc,[0]*n)
        try:
            tree=reference.tree(0);queries=[];old=[];criticalities={};edge_ids=[i*17+3 for i in range(len(dest))]
            for cid,target in enumerate(rng.sample(range(1,n),rng.randrange(1,n))):
                q=dict(connection_id=cid,net_id=5,source=0,sink=target);queries.append(q)
                answer=tree.expand(target,Fraction(1),{},2**127)
                old.append(dict(q,answer=dict(physical_edge_ids=[edge_ids[s] for s in answer['path_slots']]),budget_integer=2**127))
                value=rng.choice([Fraction(0),Fraction(1),Fraction(2,3),Fraction(1,2)])
                criticalities[cid]=dict(net=5,source_rr=0,target_rr=target,local_sink_pin=cid+1,
                    criticality_numerator=value.numerator,criticality_denominator=value.denominator)
            ledger={u:1+(seed%2 and u%4==0) for u in range(n)};prices={u:rng.randrange(20) for u in range(n)}
            slots={eid:i for i,eid in enumerate(edge_ids)}
            for threshold in [1,4,16]:
                args=(queries,old,criticalities,prices,edge_ids,ledger,[1]*n,slots,threshold)
                a=route(reference,*args);b=route(native,*args)
                assert a==b,(seed,threshold,a,b);net_cases+=1
        finally:native.close()
    assert results['UNREACHABLE'] and results['RETAIN_RAW_BUDGET'] and results['COMMITTED'] and maximum_bits>160
    f=dict(row_offsets=[0,1,1],dest_ranks=[1]);g=Compiled(f,[1],[0,0]);t=g.tree(0)
    rejected=0
    for args in [(-1,Fraction(1),{},4),(1,Fraction(2),{},4),(1,Fraction(1),{1:-1},4),
                 (1,Fraction(1,2**64),{},4),(1,Fraction(1),{},2**128)]:
        state=(dict(t.arrival),dict(t.parents))
        try:t.expand(*args)
        except ValueError:rejected+=1
        else:raise AssertionError('invalid compiled domain accepted')
        assert state==(t.arrival,t.parents)
    assert t.expand(1,Fraction(1),{},1)['committed'];g.close()
    out=R/'experiments/compiled_criticality_tree_contract_v1_2026-10-15';out.mkdir(exist_ok=False)
    report=dict(bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY),
            str(R/'tools/soft_demand_cpp/criticality_tree_exact_v2.cpp'):sha(R/'tools/soft_demand_cpp/criticality_tree_exact_v2.cpp')},
            all_pass=True,random_graphs=200,sequential_expansions=4800,retained_seed_continuations=seeded_cases,
            complete_NET_primary_comparisons=net_cases,status_counts=dict(results),maximum_objective_bits=maximum_bits,
            invalid_domain_rejections=rejected,all_results_paths_parents_arrivals_and_atomic_rejections_identical=True,
            scope='Primitive and complete NET-call exact parity, including cycles, parallel/zero-cost ties, retained branches, arbitrary rational criticalities and >160-bit objectives. No original full-design state/transaction or performance evidence yet.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='bindings'},indent=2),flush=True)


if __name__=='__main__':main()
