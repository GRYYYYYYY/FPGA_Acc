"""Exact two-limb ABI, independent Python costs, and legacy path/tie parity."""
import heapq
import json
import random
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from pre_route_endpoints import sha
from derive_wide_cost_backends_v1 import derive
from wide_cost_search_bridge_v2 import Forward, Bidirectional, Word, NONE
from lazy_compact_wide_sparse_structural_objective_search_v2 import Search
from soft_demand_workspace_bridge_v1 import Search as OldForward
from bidirectional_rc_bridge_v1 import Bidirectional as OldBidi
from bidirectional_rc_reference_v2 import Bidirectional as Reference

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
binary=R/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so'
old_forward=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
old_bidi=R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so'

def forward_reference(f,inc,initial,source,targets,prices,weight):
    n=len(f['capacities']);raw=[NONE]*n;pn=[2**64-1]*n;pe=pn.copy();settled=[0]*n
    d={source:initial};raw[source]=initial;q=[(initial,source)];remaining=set(targets)
    while q and remaining:
        cost,u=heapq.heappop(q)
        if cost!=d[u]:continue
        settled[u]=1;remaining.discard(u)
        for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
            v=f['dest_ranks'][e]
            if not f['capacities'][v]:continue
            value=cost+inc[e]+weight*prices.get(v,0)
            if v not in d or value<d[v]:
                d[v]=value;raw[v]=raw[u]+inc[e];pn[v]=u;pe[v]=e
                heapq.heappush(q,(value,v))
    return raw,pn,pe,settled

def rejected(action):
    try:action()
    except (ValueError,RuntimeError,OverflowError):return
    raise AssertionError('invalid domain accepted')

def verify():
    derivation=derive()
    bindings={**closure([Path(__file__)]),**derivation['bindings'],**{str(p):sha(p) for p in (binary,old_forward,old_bidi)}}
    counts=Counter()
    for v in (0,1,2**64-1,2**64,2**120-1,2**128-1):assert Word.of(v).integer()==v
    from wide_cost_search_bridge_v2 import Words
    packed=Words(range(10000))
    assert not packed.buffer._objects and list(packed)==list(range(10000))
    for i in range(10000):packed[i]=2**100+i
    assert not packed.buffer._objects and list(packed)==[2**100+i for i in range(10000)]
    for v in (-1,2**128,True,1.5):rejected(lambda:Word.of(v))
    for mode in ('legacy','wide'):
        for seed in range(200):
            rng=random.Random(seed);n=rng.randrange(2,35)
            f=dict(capacities=[rng.randrange(3) for _ in range(n)],row_offsets=[0],dest_ranks=[])
            f['capacities'][0]=1;inc=[]
            magnifier=1 if mode=='legacy' else 2**66
            for u in range(n):
                for _ in range(rng.randrange(n+1)):
                    f['dest_ranks'].append(rng.randrange(n));inc.append(rng.choice([0,0,1,5,19])*magnifier)
                f['row_offsets'].append(len(inc))
            rc=SimpleNamespace(increments=inc,initial=lambda u:(u%9)*magnifier)
            forward=Forward(f,rc,binary);bidi=Bidirectional(f,rc,binary);reference=Reference(f,inc)
            if mode=='legacy':oldf=OldForward(f,rc,old_forward);oldb=OldBidi(f,rc,old_bidi)
            enabled=[u for u,c in enumerate(f['capacities']) if c]
            for step in range(12):
                src,sink=rng.choice(enabled),rng.choice(enabled)
                if step==0:sink=src
                weight=[0,1,13,2**63 if mode=='legacy' else 2**67][step%4]
                pmag=magnifier if step%4 in (0,1,2) else 1
                prices={u:rng.choice([0,0,1,7])*pmag for u in range(n)}
                for s in (forward,bidi):s.prepare(prices,weight)
                result=bidi.search(src,sink)
                assert result==reference.search(src,sink,prices,weight,rc.initial(src)),(mode,seed,step)
                # A distinct forward priority-queue calculation checks the minimum.
                one=forward_reference(f,inc,rc.initial(src),src,{sink},prices,weight)
                assert (result is not None)==bool(one[3][sink])
                if result is not None:
                    u=sink;path=[]
                    while u!=src:path.append(one[2][u]);u=one[1][u]
                    assert result['objective']==one[0][sink]+weight*sum(prices[f['dest_ranks'][e]] for e in path)
                targets=set(rng.sample(range(n),rng.randrange(n+1)))
                answer=forward.search(src,targets)
                expected=forward_reference(f,inc,rc.initial(src),src,targets,prices,weight)
                assert answer[2]=={s for s in targets if expected[3][s]}
                for name,values in zip(('raw','pn','pe','settled'),expected):assert list(getattr(forward,name))==values,(mode,seed,step,name)
                if mode=='legacy':
                    oldf.prepare(prices,weight);oldb.prepare(prices,weight)
                    assert oldb.search(src,sink)==result
                    oldf.search(src,targets)
                    for name in ('raw','pn','pe','settled'):
                        values=list(getattr(oldf,name))
                        if name=='raw':values=[NONE if v==2**64-1 else v for v in values]
                        assert values==list(getattr(forward,name))
                    counts['legacy_complete_array_and_bidirectional_path_parity']+=1
                before=[list(getattr(forward,k)) for k in ('raw','pn','pe','settled')]
                rejected(lambda:forward.search(src,{n}))
                rejected(lambda:forward.prepare({0:2**119},2**119))
                assert before==[list(getattr(forward,k)) for k in ('raw','pn','pe','settled')]
                assert forward.search(src,targets)[2]==answer[2]
                counts[mode+'_sequential_queries']+=1
                counts['reachable' if result is not None else 'unreachable']+=1
            forward.close();bidi.close()
            rejected(lambda:forward.search(0,set()));rejected(lambda:bidi.search(0,0))
            if mode=='legacy':oldf.close();oldb.close()
    # Real observed Titan maximum arc and native base, with costs straddling u64.
    arc=28261273632681042050;base=41795814031964084734
    f=dict(capacities=[1,1,1,1],row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,3])
    rc=SimpleNamespace(increments=[arc,arc+1,0,0],initial=lambda u:14258774317681042050)
    s=Search(f,rc,binary,[0,base,0,0]);s.prepare({},0,structural=False)
    assert s.search(0,{3})[0][3]==rc.initial(0)+arc
    s.prepare({2:2**67},1,price_ceiling=2**68)
    assert s.search(0,{3})[1][3]==(1,2)
    s.patch_prices({2:0})
    raw,parents,found=s.search(0,{3})
    assert found=={3} and parents[3]==(2,3) and raw[3]==rc.initial(0)+arc+1
    before=(s.price_epoch,list(s.prices),s.search(0,{3}))
    rejected(lambda:s.patch_prices({0:1,2:2**68+1}))
    rejected(lambda:s.prepare({},2**119,price_ceiling=2**119))
    assert before==(s.price_epoch,list(s.prices),s.search(0,{3}))
    for backend in s.backends:
        for k,v in enumerate(s.prices if backend is s.backends[1] else [0]*4):
            assert backend.forward.price[k]==backend.bidirectional.price[k]==v
    s.close()
    # A packed owned snapshot must reject mutation and detach from caller buffers.
    from array import array
    f=dict(capacities=array('Q',[1,1]),row_offsets=array('Q',[0,1,1]),dest_ranks=array('Q',[1]))
    rc=SimpleNamespace(increments=[9],initial=lambda u:0)
    s=Search(f,rc,binary,[0,3]);s.prepare({},0)
    f['dest_ranks'][0]=0;f['row_offsets'][1]=0;rc.increments[0]=99
    assert s.search(0,{1})[0][1]==9 and s.fields['dest_ranks'][0]==1
    try:s.fields['dest_ranks'][0]=0
    except TypeError:pass
    else:raise AssertionError('mutable packed snapshot')
    s.close()
    # Sparse patches made before first engine creation must be used at first query.
    f=dict(capacities=[1,1,1],row_offsets=[0,2,3,3],dest_ranks=[1,2,2])
    rc=SimpleNamespace(increments=[0,9,0],initial=lambda u:0)
    s=Search(f,rc,binary,[0,0,0]);s.prepare({},1,price_ceiling=99)
    assert all(b.forward.backend is None and b.bidirectional.backend is None for b in s.backends)
    s.patch_prices({1:20});assert s.search(0,{2})[0][2]==9
    assert s.backends[1].bidirectional.backend is not None and s.backends[1].forward.backend is None
    s.patch_prices({1:0});assert s.search(0,{1,2})[0][2]==0
    assert s.backends[1].forward.backend is not None
    assert s.backends[0].forward.backend is None and s.backends[0].bidirectional.backend is None
    s.close()
    # Near the admitted ceiling: no carry loss in >100-bit raw results.
    rc=SimpleNamespace(increments=[2**110],initial=lambda u:2**109)
    f=dict(capacities=[1,1],row_offsets=[0,1,1],dest_ranks=[1])
    for cls in (Forward,Bidirectional):
        s=cls(f,rc,binary);s.prepare({},0)
        result=s.search(0,{1}) if cls is Forward else s.search(0,1)
        assert (result[0][1] if cls is Forward else result['raw'])==3*2**109
        rejected(lambda:s.prepare({1:2**119},2));s.close()
    assert all(sha(p)==h for p,h in bindings.items())
    return dict(bindings=bindings,all_pass=True,counts=dict(counts),two_limb_abi_exact=True,
                titan_observed_cost_sparse_patch_fixture_pass=True,over_envelope_and_invalid_patch_preserve_prepared_state=True,
                scope='Primitive/storage parity, independent costs, full forward arrays and bidirectional path/ties. Full real-model frames/events require separate evidence.')

if __name__=='__main__':
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    result=verify();(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)
