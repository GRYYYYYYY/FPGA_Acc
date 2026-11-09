"""Actual skipped expansions versus uncached arbitrary-integer tree execution."""
import json,random,resource,sys
from collections import Counter
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from criticality_tree_dependency_cache_v1 import Graph
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from source_binding_v2 import closure


def main():
    resource.setrlimit(resource.RLIMIT_AS,(512*2**20,512*2**20));counts=Counter();maxbits=0
    rng=random.Random(20261015)
    for trial in range(200):
        n=rng.randrange(5,24);rows=[0];dest=[];increments=[]
        for u in range(n):
            for v in range(n-1):
                if u<n-1 and (v==(u+1)%(n-1) or rng.random()<.12):
                    dest.append(v);increments.append(rng.choice([0,1,7,2**70]))
            rows.append(len(dest))
        fields=dict(row_offsets=rows,dest_ranks=dest);initial=[2**65+i for i in range(n)]
        cached=Graph(fields,increments,initial,entries=3);reference=Reference(fields,increments,initial)
        prices={i:rng.randrange(20)+2**110 for i in range(n)}
        seed=reference.tree(0)
        if trial%2:seed.expand(1,Fraction(1),prices,2**120)
        def fresh(graph,keep_seed=True):
            tree=graph.tree(0)
            if keep_seed:tree.arrival=dict(seed.arrival);tree.parents=dict(seed.parents)
            return tree
        def check(tree,other,target,c,p,b):
            nonlocal maxbits
            a=tree.expand(target,c,p,b);z=other.expand(target,c,p,b)
            assert a==z and tree.arrival==other.arrival and tree.parents==other.parents
            if 'objective_numerator' in a:maxbits=max(maxbits,a['objective_numerator'].bit_length())
            counts['complete_result_and_post_state_comparisons']+=1
            assert cached.items==sum(x['items'] for x in cached.cache.values()) and len(cached.cache)<=cached.entries and cached.items<=cached.total_limit
            return a
        for step in range(6):
            target=n-1 if step==0 else rng.randrange(n-1)
            c=[Fraction(0),Fraction(1),Fraction(3,7),Fraction(2**31,2**32-1)][step%4];budget=0 if step%3==1 else 2**120
            tree=fresh(cached);ans=check(tree,fresh(reference),target,c,prices,budget)
            key=next(reversed(cached.cache));entry=cached.cache[key];depends=dict(entry['reads'])
            # Returned objects and post-state maps must not poison cached output.
            ans['status']='POISON';tree.arrival.clear();tree.parents.clear()
            hits=cached.stats['hits'];calls=cached.stats['actual_searches']
            check(fresh(cached),fresh(reference),target,c,prices,budget)
            assert cached.stats['hits']==hits+1 and cached.stats['actual_searches']==calls;counts['actual_search_skips']+=1
            unread={i:v if i in depends else max(0,v-2**109) for i,v in prices.items()}
            hits=cached.stats['hits'];check(fresh(cached),fresh(reference),target,c,unread,budget)
            assert cached.stats['hits']==hits+1;counts['unread_price_decrease_hits']+=1
            if depends:
                changed=dict(prices);node=min(depends);changed[node]-=2**109;miss=cached.stats['misses']
                check(fresh(cached),fresh(reference),target,c,changed,budget)
                assert cached.stats['misses']==miss+1;counts['observed_price_decrease_misses']+=1
            # Budget and criticality changes always use separate query keys.
            miss=cached.stats['misses'];check(fresh(cached),fresh(reference),target,c,prices,budget+1)
            assert cached.stats['misses']==miss+1;counts['budget_key_misses']+=1
            miss=cached.stats['misses'];check(fresh(cached),fresh(reference),target,1-c,prices,budget)
            assert cached.stats['misses']==miss+1;counts['criticality_key_misses']+=1
            if len(seed.arrival)>1:
                miss=cached.stats['misses'];check(fresh(cached,False),fresh(reference,False),target,c,prices,budget)
                assert cached.stats['misses']==miss+1;counts['changed_seed_misses']+=1
        counts['evictions']+=cached.stats['evictions']
    # Fixed chain forces incomplete trace, oversize output and disabled caches
    # to compute exact full answers instead of using partial dependencies.
    fields=dict(row_offsets=[0,1,2,2],dest_ranks=[1,2]);reference=Reference(fields,[1,1],[0]*3)
    for options,label in [({'read_limit':0},'incomplete_read_trace'),({'state_limit':1},'oversize_entry'),({'total_limit':0},'oversize_entry'),({'entries':0},'uncached_seed_or_disabled')]:
        graph=Graph(fields,[1,1],[0]*3,**options)
        for _ in range(3):
            t=graph.tree(0);r=reference.tree(0);assert t.expand(2,Fraction(1,2),{},10)==r.expand(2,Fraction(1,2),{},10);assert t.parents==r.parents and t.arrival==r.arrival
        assert not graph.cache and graph.stats[label]==3;counts['bounded_exact_fallbacks']+=3
    assert counts['actual_search_skips']==1200 and counts['unread_price_decrease_hits']==1200 and counts['evictions']>0 and maxbits>128
    out=R/'experiments/criticality_tree_dependency_cache_contract_v1_2026-10-15';out.mkdir()
    report=dict(bindings=closure([Path(__file__)]),all_pass=True,random_graphs=200,counts=dict(counts),maximum_observed_objective_bits=maxbits,scope='Pure serial nonnegative price snapshots; current immutable graph instance and complete pre-search tree state, criticality and raw budget keyed. Actual reference expansions skipped with exact result/post-state comparison, including rejects and unreachable. Item-count quotas, not byte-residency bounds. No compiled integration, full design, timing gain, live stale-context or impure callback guarantee.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'},indent=2),flush=True)


if __name__=='__main__':main()
