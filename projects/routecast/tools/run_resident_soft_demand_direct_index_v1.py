"""Endpoint-only shared rooted RC trees; overuse is measured demand, not a legal route."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from direct_index_rc_endpoint_context_v1 import load_endpoints
from soft_demand_cpp_bridge_v1 import Search

def predict(endpoint,output):
 begin=time.perf_counter();endpoint=Path(endpoint).resolve();out=Path(output).resolve();out.mkdir(parents=True);bindings={**closure([Path(__file__)]),str(endpoint):sha(endpoint)};bindings.update({v['path']:v['sha256'] for v in json.loads(endpoint.read_text())['inputs'].values()});graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);floors={};groups=defaultdict(list);binary=R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so';contract=R/'experiments/soft_demand_cpp_contract_v1_2026-10-07/verification.json';proof=json.loads(contract.read_text());assert proof['actual_python_block_random_cases']==200 and proof['bindings'][str(binary)]==sha(binary);bindings.update({str(binary):sha(binary),str(contract):sha(contract),str(R/'tools/soft_demand_cpp/tree_v1.cpp'):sha(R/'tools/soft_demand_cpp/tree_v1.cpp')});search=Search(f,rc,binary);search.prepare({},0);model_setup_seconds=time.perf_counter()-begin;initial_tick=time.perf_counter();cpp_search_seconds=0.0;cpp_prepare_seconds=0.0;ledger_check_seconds=0.0
 for q in queries:groups[q['net_id']].append(q)
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,rounds=2,price_unit_integer=rc.scale//(20*10**9),static_channel_span_price_ns='1/20 per destination CHAN span, applied in feedback only; initial remains exact zero-price RC floor',policy='One resident original positive-capacity graph/exact integer RC context. Recompute minimum floors by zero-price shortest rooted tree, derive max(1ns,ceil1.5floor) budgets. No archived floor/sketch/native labels read. Complete initial demand, then fixed two 50ps-price rounds, ascending affectedNETs, all original queries, budget-safe whole tree replacement and retained old epochs on failure. Cached ownership and affected-node prevalidated ledger updates (no full Counter copy per transaction); full ledger checks at round boundaries. Demand can overflow; not legal joint route or whole native workflow.',required_connections=len(queries)),indent=2)+'\n');records=[];owners={};independent=Counter();failures=[]
 for net,qs in sorted(groups.items()):
  assert len({q['source'] for q in qs})==1;src=qs[0]['source'];tick=time.perf_counter();d,parents,settled=search.search(src,{q['sink'] for q in qs});cpp_search_seconds+=time.perf_counter()-tick
  if any(q['sink'] not in settled for q in qs):raise RuntimeError('Initial floor unreachable; complete-feedback gate failed, no omitted query acceptance')
  for q in qs:floors[q['source'],q['sink']]=d[q['sink']]
  budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs}
  owned=set()
  for q in sorted(qs,key=lambda q:q['connection_id']):
   if q['sink'] not in settled or d[q['sink']]>budgets[q['connection_id']]:failures.append(dict(query=q,status='BUDGET_UNREACHABLE'));continue
   u=q['sink'];path=[];used={u}
   while u!=src:
    previous,e=parents[u];path.append(f['edge_ids'][e]);u=previous;assert u not in used;used.add(u)
   path.reverse();assert rc.path(src,q['sink'],path)==d[q['sink']];owned.update(used);independent.update(used);records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budgets[q['connection_id']],floor_integer=floors[src,q['sink']]))
  owners[net]=owned
 ledger=Counter(n for owned in owners.values() for n in owned);overflow=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());candidate=dict(status='COMPLETE_DEMAND_SKETCH' if not failures else 'INCOMPLETE_DEMAND_SKETCH',records=records,ledger=dict(ledger),independent_connection_ledger=dict(independent),completed_connections=len(records),required_connections=len(queries),failure=failures[0] if failures else None,failures=failures,overflow_units=overflow,overflow_nodes=sum(c>f['capacities'][n] for n,c in ledger.items()),eligible_for_legal_route_commit=False,graph_sha256=digest,scope='Complete endpoint demand estimate with possible cross-NET overuse; no route acceptance.')
 assert not failures and len(records)==len(queries)
 seed=candidate;(out/'initial.json').write_text(json.dumps(seed)+'\n');(out/'floors.json').write_text(json.dumps([dict(source=s,sink=t,minimum_integer=v) for (s,t),v in sorted(floors.items())])+'\n');initial_seconds=time.perf_counter()-initial_tick;feedback_tick=time.perf_counter();slots=rc.edge_slots;records=defaultdict(list)
 for x in seed['records']:records[x['net_id']].append(x)
 def own(recs):return {x['source'] for x in recs}|{f['dest_ranks'][slots[e]] for x in recs for e in x['answer']['physical_edge_ids']}
 def rebuild():return Counter(n for recs in records.values() for n in own(recs))
 owned={n:own(recs) for n,recs in records.items()};ledger=rebuild();assert dict(ledger)=={int(n):c for n,c in seed['ledger'].items()};span_prices={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in {'CHANX','CHANY'}};prices=Counter(span_prices);epochs={n:1 for n in groups};weight=rc.scale//(20*10**9);assert weight>0;rounds=[]
 for round_index in range(2):
  changed={n:max(0,c-f['capacities'][n]) for n,c in ledger.items() if c>f['capacities'][n]};prices.update(changed);prepare_tick=time.perf_counter();search.prepare(prices,weight);cpp_prepare_seconds+=time.perf_counter()-prepare_tick;affected=sorted(n for n in groups if owned[n].intersection(set(changed)|set(span_prices) if round_index==0 else changed));events=[];before=sum(changed.values());round_start=time.perf_counter()
  for net in affected:
   qs=sorted(groups[net],key=lambda q:q['connection_id']);src=qs[0]['source'];assert all(q['source']==src for q in qs);search_tick=time.perf_counter();raw,parents,settled=search.search(src,{q['sink'] for q in qs});cpp_search_seconds+=time.perf_counter()-search_tick
   oldepoch=epochs[net];old=records[net];bad=[q['connection_id'] for q in qs if q['sink'] not in settled or raw[q['sink']]>next(x['budget_integer'] for x in old if x['connection_id']==q['connection_id'])]
   event=dict(net_id=net,old_epoch=oldepoch,new_epoch=oldepoch,status='RETAIN_BUDGET_OR_UNREACHABLE' if bad else 'COMMITTED',failed_connection_ids=bad)
   if not bad:
    candidate=[];oldbyid={x['connection_id']:x for x in old}
    for q in qs:
     u=q['sink'];path=[];seen={u}
     while u!=src:
      previous,edge=parents[u];path.append(f['edge_ids'][edge]);u=previous;assert u not in seen;seen.add(u)
     path.reverse();delay=rc.path(src,q['sink'],path);assert delay==raw[q['sink']]<=oldbyid[q['connection_id']]['budget_integer'];candidate.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=delay),budget_integer=oldbyid[q['connection_id']]['budget_integer'],floor_integer=oldbyid[q['connection_id']]['floor_integer']))
    newowned=own(candidate);removed=owned[net]-newowned;added=newowned-owned[net]
    # Validate every affected count before touching the shared ledger.
    updates={node:ledger[node]-1 for node in removed};updates.update({node:ledger[node]+1 for node in added});assert all(value>=0 for value in updates.values())
    for node,value in updates.items():
     if value:ledger[node]=value
     else:del ledger[node]
    records[net]=candidate;owned[net]=newowned;epochs[net]+=1;event['new_epoch']=epochs[net];event['records']=candidate
   assert sum(map(len,records.values()))==len(queries);events.append(event)
  check_tick=time.perf_counter();assert ledger==rebuild();assert ledger==Counter(n for owned_nodes in owned.values() for n in owned_nodes);ledger_check_seconds+=time.perf_counter()-check_tick
  state=dict(records=sorted([x for recs in records.values() for x in recs],key=lambda x:x['connection_id']),ledger=dict(ledger),epochs=epochs.copy(),prices=dict(prices));file=out/f'round{round_index}.json';file.write_text(json.dumps(state)+'\n');after=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());rounds.append(dict(round_index=round_index,changed_nodes=changed,affected_nets=affected,events=events,overflow_before=before,overflow_after=after,state_file=str(file),seconds=time.perf_counter()-round_start));print('FEEDBACK ROUND',out.name,round_index,len(affected),sum(x['status']=='COMMITTED' for x in events),before,after,flush=True)
 final=state;independent=Counter()
 for x in final['records']:independent.update(own([x]))
 candidate=dict(seed,records=final['records'],ledger=final['ledger'],independent_connection_ledger=dict(independent),overflow_units=after,overflow_nodes=sum(c>f['capacities'][int(n)] for n,c in final['ledger'].items()),status='COMPLETE_DEMAND_SKETCH',eligible_for_legal_route_commit=False);(out/'sketch.json').write_text(json.dumps(candidate)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rounds=rounds,total_paid_resident_seconds=time.perf_counter()-begin,model_setup_seconds=model_setup_seconds,initial_seconds=initial_seconds,feedback_seconds=time.perf_counter()-feedback_tick,cpp_prepare_seconds=cpp_prepare_seconds,cpp_search_seconds=cpp_search_seconds,ledger_check_seconds=ledger_check_seconds,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('FEEDBACK DONE',out.name,after,flush=True)

 return dict(completed=len(queries),overflow_units=after,total_paid_resident_seconds=time.perf_counter()-begin)
if __name__=='__main__':print(json.dumps(predict(*sys.argv[1:])),flush=True)
