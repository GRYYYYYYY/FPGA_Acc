"""Independent full recomputation, shortest paths and transaction restoration."""
import random,heapq,json,sys
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
from sparse_structural_objective_search_v1 import Search
from present_occupancy_context_v1 import Context
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';totals=Counter()
for seed in range(100):
 rng=random.Random(5000+seed);n=rng.randrange(6,24);f=dict(row_offsets=[0],dest_ranks=[],edge_ids=[],capacities=[rng.randrange(1,4) for _ in range(n)]);inc=[]
 for u in range(n):
  for v in range(n):
   if v==(u+1)%n or rng.random()<.15:f['dest_ranks'].append(v);f['edge_ids'].append(len(inc));inc.append(rng.randrange(5))
  f['row_offsets'].append(len(inc))
 base=[rng.randrange(8) for _ in range(n)];rc=SimpleNamespace(initial=lambda u:0,increments=inc);s=Search(f,rc,binary,base);c=Context(s,f['capacities'],base,6)
 owners=[set(rng.sample(range(n),rng.randrange(1,n))) for _ in range(6)];ledger=Counter(node for old in owners for node in old)
 for round_index in range(2):
  history={u:rng.randrange(8) for u in range(n)};weight=rng.choice([0,1,17]);c.start_round(history,weight,ledger)
  for step in range(12):
   net=rng.randrange(6);old=owners[net];view=c.begin(old);src=min(old);targets=set(rng.sample(range(n),rng.randrange(1,5)))
   expected={u:weight*history[u]+base[u]*max(0,ledger[u]-(u in old)-f['capacities'][u]+1) for u in range(n)}
   assert all(view.get(u)==s.prices[u]==expected[u] for u in range(n))
   raw,parents,found=s.search(src,targets);distance={src:0};q=[(0,src)]
   while q:
    cost,u=heapq.heappop(q)
    if cost!=distance[u]:continue
    for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     v=f['dest_ranks'][slot];cost2=cost+inc[slot]+base[v]+expected[v]
     if cost2<distance.get(v,2**120):distance[v]=cost2;heapq.heappush(q,(cost2,v))
   assert found==targets;new={src}
   for target in targets:
    assert s.last_objectives[target]==distance[target];u=target;delay=0;seen={u}
    while u!=src:
     prev,slot=parents[u];assert f['row_offsets'][prev]<=slot<f['row_offsets'][prev+1] and f['dest_ranks'][slot]==u;delay+=inc[slot];new.add(u);u=prev;assert u not in seen;seen.add(u)
    assert delay==raw[target];totals['paths']+=1
   try:c.begin(old)
   except RuntimeError:pass
   else:raise AssertionError('nested transaction accepted')
   before=dict(c.ledger);beforeprices=list(s.prices)
   try:c.finish({0:1,n:1})
   except ValueError:pass
   else:raise AssertionError('invalid finish accepted')
   assert dict(c.ledger)==before and s.prices==beforeprices and view.get(0)==expected[0]
   if rng.random()<.5:
    updates={u:ledger[u]-1 for u in old-new};updates.update({u:ledger[u]+1 for u in new-old});c.finish(updates);owners[net]=new;ledger=Counter(u for own in owners for u in own);totals['commits']+=1
   else:c.finish();totals['retains']+=1
   assert c.ledger==ledger
   for u in range(n):assert s.prices[u]==weight*history[u]+base[u]*max(0,ledger[u]-f['capacities'][u]+1)
   try:view.get(0)
   except RuntimeError:pass
   else:raise AssertionError('stale snapshot accepted')
   totals['transactions']+=1
 s.close()
from structural_actual_old_fallback_adapter_v1 import fallback
f=dict(row_offsets=[0,2,4,6,6,6],dest_ranks=[1,2,3,4,3,4],edge_ids=list(range(6)),capacities=[1]*5)
inc=[1]*6;rc=SimpleNamespace(initial=lambda u:0,increments=inc,increment=lambda slot:inc[slot],path=lambda source,sink,path:sum(inc[e] for e in path));base=[0,2,1,0,0]
s=Search(f,rc,binary,base);c=Context(s,f['capacities'],base,2)
queries=[dict(connection_id=0,net_id=0,source=0,sink=3),dict(connection_id=1,net_id=0,source=0,sink=4)]
old=[dict(q,answer=dict(status='FOUND',physical_edge_ids=[0,2+i],delay=2),budget_integer=2,floor_integer=2) for i,q in enumerate(queries)];parents={2:(0,1),3:(2,4),4:(2,5)}
c.start_round({},0,{0:1,1:1,2:1,3:1,4:1});view=c.begin({0,1,3,4})
a=fallback(f,rc,{i:i for i in range(6)},queries,old,parents,{3,4},view,1,base)
assert view.get(1)==0 and view.get(2)==1 and a['status']=='RETAIN' and a['old_union_cost']==a['chosen_union_cost']==5
c.finish();c.start_round({},0,{0:1,1:1,3:1,4:1});view=c.begin({0,1,3,4})
b=fallback(f,rc,{i:i for i in range(6)},queries,old,parents,{3,4},view,1,base)
assert b['status']=='ACCEPT_STRICT_IMPROVEMENT' and b['old_union_cost']==5 and b['chosen_union_cost']==4
assert all(x['answer']['delay']==2 for x in b['records']);c.finish();s.close()
O=R/'experiments/present_occupancy_context_contract_v1_2026-10-10';O.mkdir(exist_ok=True)
bindings={**closure([Path(__file__)]),str(binary):sha(binary)};p=R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so';bindings[str(p)]=sha(p)
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,graphs=100,counts=dict(totals),all_owner_exclusion_prices_minimum_objectives_and_finish_rebuilds_pass=True,shared_fallback_same_snapshot_and_raw_budget_fixture_pass=True,scope='Serial random occupancy transactions; commits intentionally arbitrary to cover updates. Hand-computed fallback fixture included; not real graph, complete budget/overflow guard feedback, native or performance proof.'),indent=2)+'\n')
print('PRESENT OCCUPANCY CONTEXT PASS',totals)
