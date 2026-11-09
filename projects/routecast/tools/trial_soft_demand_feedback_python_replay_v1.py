"""Two frozen rounds of affected-NET soft demand feedback, complete budget-safe replacement."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
name=sys.argv[1];out=R/f'experiments/mcnc_soft_demand_feedback_python_replay_v1_2026-10-07/{name}';out.mkdir(parents=True);begin=time.perf_counter();parent=R/f'experiments/mcnc_budgeted_soft_demand_v1_2026-10-07/{name}';vp=parent/'verification.json';v=json.loads(vp.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];sp=parent/'sketch.json';assert sha(sp)==v['bindings'][str(sp)];seed=json.loads(sp.read_text());ep=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json';fp=R/f'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/{name}/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(sp):sha(sp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()});bindings[str(R/'tools/trial_soft_demand_feedback_v1.py')]=sha(R/'tools/trial_soft_demand_feedback_v1.py');_,digest,nodes,f,rc,queries=load_endpoints(ep);slots={eid:e for e,eid in enumerate(f['edge_ids'])};groups=defaultdict(list);records=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
for x in seed['records']:records[x['net_id']].append(x)
def own(recs):return {x['source'] for x in recs}|{f['dest_ranks'][slots[e]] for x in recs for e in x['answer']['physical_edge_ids']}
def rebuild():return Counter(n for recs in records.values() for n in own(recs))
owned={n:own(recs) for n,recs in records.items()};ledger=rebuild();assert dict(ledger)=={int(n):c for n,c in seed['ledger'].items()};prices=Counter();epochs={n:1 for n in groups};weight=rc.scale//(20*10**9);assert weight>0;protocol=dict(bindings=bindings,rounds=2,price_unit_integer=weight,policy='At round boundary increment prices at ALL overused nodes by overuse units; freeze prices for whole round. Affected NET if old union intersects changed nodes. Ascending NET replay; weighted RC+destination-price shortest singleparent tree on positive-cap graph, all sinks checked against unchanged original RC budgets. Any budget failure retains ENTIRE old NET tree/ledger/epoch. Complete valid replacement subtracts old uniqueNET ownership and adds new; demand may still overflow, never legal route commit. Full ledger rebuilt after each transaction. Unaffected NETs retained; no full reoptimization equivalence claim. Native labels excluded. Fixed two rounds, no retuning.',required_connections=len(queries));(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rounds=[]
for round_index in range(2):
 changed={n:max(0,c-f['capacities'][n]) for n,c in ledger.items() if c>f['capacities'][n]};prices.update(changed);affected=sorted(n for n in groups if owned[n].intersection(changed));events=[];before=sum(changed.values());round_start=time.perf_counter()
 for net in affected:
  qs=sorted(groups[net],key=lambda q:q['connection_id']);src=qs[0]['source'];assert all(q['source']==src for q in qs);d={src:rc.initial(src)};raw={src:rc.initial(src)};parents={};queue=[(d[src],src)];sinks={q['sink'] for q in qs};settled=set()
  while queue and sinks-settled:
   cost,u=heapq.heappop(queue)
   if cost!=d[u]:continue
   settled.add(u)
   for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    dest=f['dest_ranks'][edge]
    if f['capacities'][dest]<=0:continue
    value=cost+rc.increments[edge]+weight*prices[dest]
    if value<d.get(dest,1<<120):d[dest]=value;raw[dest]=raw[u]+rc.increments[edge];parents[dest]=(u,edge);heapq.heappush(queue,(value,dest))
  oldepoch=epochs[net];old=records[net];bad=[q['connection_id'] for q in qs if q['sink'] not in settled or raw[q['sink']]>next(x['budget_integer'] for x in old if x['connection_id']==q['connection_id'])]
  event=dict(net_id=net,old_epoch=oldepoch,new_epoch=oldepoch,status='RETAIN_BUDGET_OR_UNREACHABLE' if bad else 'COMMITTED',failed_connection_ids=bad)
  if not bad:
   candidate=[];oldbyid={x['connection_id']:x for x in old}
   for q in qs:
    u=q['sink'];path=[];seen={u}
    while u!=src:
     previous,edge=parents[u];path.append(f['edge_ids'][edge]);u=previous;assert u not in seen;seen.add(u)
    path.reverse();delay=rc.path(src,q['sink'],path);assert delay==raw[q['sink']]<=oldbyid[q['connection_id']]['budget_integer'];candidate.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=delay),budget_integer=oldbyid[q['connection_id']]['budget_integer'],floor_integer=oldbyid[q['connection_id']]['floor_integer']))
   newowned=own(candidate);nextledger=Counter(ledger)
   for node in owned[net]-newowned:
    nextledger[node]-=1;assert nextledger[node]>=0
    if not nextledger[node]:del nextledger[node]
   for node in newowned-owned[net]:nextledger[node]+=1
   records[net]=candidate;owned[net]=newowned;ledger=nextledger;epochs[net]+=1;event['new_epoch']=epochs[net];event['records']=candidate
  assert ledger==rebuild();assert sum(map(len,records.values()))==len(queries);events.append(event)
 state=dict(records=sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id']),ledger=dict(ledger),epochs=epochs.copy(),prices=dict(prices));file=out/f'round{round_index}.json';file.write_text(json.dumps(state)+'\n');after=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());rounds.append(dict(round_index=round_index,changed_nodes=changed,affected_nets=affected,events=events,overflow_before=before,overflow_after=after,state_file=str(file),seconds=time.perf_counter()-round_start));print('FEEDBACK ROUND',name,round_index,len(affected),sum(x['status']=='COMMITTED' for x in events),before,after,flush=True)
final=state;independent=Counter()
for x in final['records']:independent.update(own([x]))
candidate=dict(seed,records=final['records'],ledger=final['ledger'],independent_connection_ledger=dict(independent),overflow_units=after,overflow_nodes=sum(c>f['capacities'][int(n)] for n,c in final['ledger'].items()),status='COMPLETE_DEMAND_SKETCH',eligible_for_legal_route_commit=False);(out/'sketch.json').write_text(json.dumps(candidate)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rounds=rounds,total_paid_feedback_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('FEEDBACK DONE',name,after,flush=True)
