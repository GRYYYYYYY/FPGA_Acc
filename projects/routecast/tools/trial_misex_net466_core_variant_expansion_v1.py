"""Focused whole-NET query-order and single-resource diversification; full batch only."""
import sys,json,time,copy
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from tree_floor_pareto_affected_seed_v13 import predict
from tree_variant_capacity_packing_v1 import pack_variants
parent=R/'experiments/misex_net466_tree_pool_v4_2026-10-07';out=R/'experiments/misex_net466_core_variant_expansion_v1_2026-10-07';out.mkdir();begin=time.perf_counter();rp=parent/'receipt.json';pr=json.loads(rp.read_text());coreproof=R/'experiments/misex_net466_pool_core_v1_2026-10-07/verification.json';core=json.loads(coreproof.read_text());assert core['core_nets']==[258,384,466] and core['irreducible_finite_pool_core'];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(rp):sha(rp),str(coreproof):sha(coreproof),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()});event=json.loads((parent/'event.json').read_text());assert sha(parent/'event.json')==pr['files'][str(parent/'event.json')];bindings[str(parent/'event.json')]=sha(parent/'event.json');binary=R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute';cpp=R/'tools/capped_bound_worker_cpp_v2/main.cpp';bindings[str(binary)]=sha(binary);bindings[str(cpp)]=sha(cpp);pools=[]
for a in pr['attempts']:
 p=parent/f"pool_attempt{a['index']}.json";assert sha(p)==pr['files'][str(p)];bindings[str(p)]=sha(p);pools.append(dict(index=a['index'],release=a['release'],options={int(net):ops for net,ops in json.loads(p.read_text()).items()}))
(out/'event.json').write_text(json.dumps(event)+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);floors={(row['source'],row['sink']):row['minimum_integer'] for row in json.loads(fp.read_text())};slots={edge:i for i,edge in enumerate(f['edge_ids'])};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];core_nets=core['core_nets'];groups=defaultdict(list)
for rec in event['before_records']:
 if rec['net_id'] in core_nets:groups[rec['net_id']].append({k:rec[k] for k in ['connection_id','net_id','source','sink']})
for q in event['selection']['queries']:groups[q['net_id']].append(q)
base=pools[0];schedule_by_net={}
for net in core_nets:
 qs=sorted(groups[net],key=lambda q:q['connection_id']);orders=[]
 for order in [qs,qs[::-1],sorted(qs,key=lambda q:(-floors[q['source'],q['sink']],q['connection_id'])),sorted(qs,key=lambda q:(floors[q['source'],q['sink']],q['connection_id'])),qs[1:]+qs[:1]]:
  if [q['connection_id'] for q in order] not in [[q['connection_id'] for q in old] for old in orders]:orders.append(order)
 own=Counter(n for option in base['options'][net] for n in option['nodes']);peer=Counter(n for other in core_nets if other!=net for option in base['options'][other] for n in option['nodes']);protected={q[k] for q in qs for k in ['source','sink']};ranked=sorted((n for n in own if peer[n] and n not in protected and nodes[n].get('type') in ('CHANX','CHANY','IPIN','OPIN')),key=lambda n:(-own[n]*peer[n],n));schedule=[dict(net=net,queries=order,banned_nodes=[]) for order in orders]
 for banned in ranked[:5]:
  for order in orders[:3]:schedule.append(dict(net=net,queries=order,banned_nodes=[banned]))
 schedule_by_net[net]=schedule[:20]
schedule=[schedule_by_net[n][i] for i in range(20) for n in core_nets if i<len(schedule_by_net[n])];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,schedule=schedule,generation_deadline_seconds=120,solver_shared_seconds=120,solver_nodes_per_call=100000,scope='Same four complete compact palettes; generate only complete NET258/384/466 alternatives against first-scope fixed kept, original budgets/caps. Round-robin order variants and up to5highest peer-overlap single-node bans; no actual NET drop or partial candidate acceptance. Direct compact inputs bound, inherited histories are provenance, new paths/candidates require independent physical audit. Paid main includes every stage; post-outcome diagnosis, not native/heldout/workflow gain.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256)
# The immutable loader graph identity is authoritative for the worker.
kept=[r for r in event['before_records'] if r['net_id'] not in base['release']];deadline=time.perf_counter()+120;attempts=[];packing=[];solution=None;solver_paid=0
def occupied(records):return {r['source'] for r in records}|{f['dest_ranks'][slots[e]] for r in records for e in r['answer']['physical_edge_ids']}
def pack_all():
 global solver_paid
 for pool in pools:
  owners=defaultdict(set);fixed=[r for r in event['before_records'] if r['net_id'] not in pool['release']]
  for rec in fixed:owners[rec['net_id']].update(occupied([rec]))
  ledger=Counter(n for own in owners.values() for n in own);start=time.perf_counter();result=pack_variants(f['capacities'],ledger,{net:[option['nodes'] for option in options] for net,options in pool['options'].items()},max_nodes=100000,deadline=start+max(0,120-solver_paid));solver_paid+=time.perf_counter()-start;packing.append(dict(after_generation=len(attempts),pool=pool['index'],result=result))
  if result['status']=='FOUND_POOL_BATCH':
   chosen={net:pool['options'][net][i] for net,i in result['chosen_option_indices'].items()};records=fixed+[rec for option in chosen.values() for rec in option['records']];expected={r['connection_id'] for r in event['before_records']}|set(event['selection']['requested_connection_ids']);assert {r['connection_id'] for r in records}==expected
   for option in chosen.values():ledger.update(option['nodes'])
   return dict(records=sorted(records,key=lambda r:r['connection_id']),ledger={n:c for n,c in ledger.items() if c},completed_connections=len(records),required_connections=len(queries),failure=None,pending_connection_ids=sorted({q['connection_id'] for q in queries}-expected),selected_origins={str(net):option['origin'] for net,option in chosen.items()},released_net_ids=pool['release'])
 return None
try:
 for index,plan in enumerate(schedule):
  if time.perf_counter()>=deadline:break
  net=plan['net'];state=predict(cache.fields,cache.rc,plan['queries'],floors,seed_records=kept,deadline=deadline,spans=spans,penalty=4*(rc.scale//10**11),remaining_cache=cache,forbidden_by_net={net:frozenset(plan['banned_nodes'])});d=out/f'generation{index}';d.mkdir();statefile=d/f'net{net}.json';statefile.write_text(json.dumps(state)+'\n');new=False
  if state['failure'] is None:
   records=sorted([r for r in state['records'] if r['net_id']==net],key=lambda r:r['connection_id']);assert {r['connection_id'] for r in records}=={q['connection_id'] for q in groups[net]};signature=tuple((r['connection_id'],tuple(r['answer']['physical_edge_ids'])) for r in records)
   for pool in pools:
    old={tuple((r['connection_id'],tuple(r['answer']['physical_edge_ids'])) for r in option['records']) for option in pool['options'][net]}
    if signature not in old:pool['options'][net].append(dict(records=copy.deepcopy(records),origin=str(statefile),nodes=sorted(occupied(records))));new=True
  attempts.append(dict(index=index,plan=plan,state_file=str(statefile),failure=state['failure'],added_variant=new));print('Generate',index,net,state['failure'],new,flush=True)
  if new:solution=pack_all()
  if solution is not None:break
 cache.finalize()
finally:
 if not cache._closed:cache.abort()
for pool in pools:(out/f"pool_attempt{pool['index']}.json").write_text(json.dumps({str(n):options for n,options in pool['options'].items()})+'\n')
(out/'candidate.json').write_text(json.dumps(solution)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,attempts=attempts,packing=packing,completed=None if solution is None else len(solution['records']),required=len(queries),solver_seconds=solver_paid,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
