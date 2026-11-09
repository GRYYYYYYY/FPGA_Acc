"""Restore every released NET after verified whole-core owner-release proposal."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from tree_floor_pareto_affected_seed_v13 import predict
out=R/'experiments/misex_net466_budget_path_owner_joint_v2_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_budget_path_owner_release_v2_2026-10-07';vp=parent/'verification.json';v=json.loads(vp.read_text());assert v['whole_net_owner_release_and_fixed_seed_plus_core_capacity_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({row['path']:row['sha256'] for row in json.loads(ep.read_text())['inputs'].values()})
for name in ['event.json','core_options.json','proposals.json']:bindings[str(parent/name)]=sha(parent/name)
for asset in [R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute',R/'tools/capped_bound_worker_cpp_v2/main.cpp']:bindings[str(asset)]=sha(asset)
event=json.loads((parent/'event.json').read_text());proposals=json.loads((parent/'proposals.json').read_text());options={int(n):ops for n,ops in json.loads((parent/'core_options.json').read_text()).items()};(out/'event.json').write_text(json.dumps(event)+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];core={258,384,466};schedules=[]
for index,proposal in enumerate(proposals):
 groups=defaultdict(list)
 for rec in event['before_records']:
  if rec['net_id'] in proposal['release'] and rec['net_id'] not in core:groups[rec['net_id']].append({k:rec[k] for k in ['connection_id','net_id','source','sink']})
 for group in groups.values():group.sort(key=lambda q:q['connection_id'])
 orders=[];nets=sorted(groups)
 for order in [nets,nets[::-1],sorted(nets,key=lambda n:(-len(groups[n]),n)),sorted(nets,key=lambda n:(len(groups[n]),n)),sorted(nets,key=lambda n:(n not in proposal['extra_owners'],n)),sorted(nets,key=lambda n:(-max(floors[q['source'],q['sink']] for q in groups[n]),n)),nets[1:]+nets[:1],nets[-1:]+nets[:-1]]:
  if order not in orders:orders.append(order)
 schedules.append([dict(proposal_index=index,net_order=order,queries=[q for n in order for q in groups[n]]) for order in orders])
schedule=[schedules[i][j] for j in range(8) for i in range(len(schedules)) if j<len(schedules[i])];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,schedule=schedule,shared_search_deadline_seconds=120,max_labels=10000,penalty_integer=4*(rc.scale//10**11),scope='Verified core shortest trees seeded with unchanged kept; all originally released and newly released owner NET connections restored in full. Original budgets/caps; no dropping connections, partial route commits or prior nine-owner scope equivalence. Paid total includes preflight/search/finalize; upstream proposal/audit and native excluded; post-outcome diagnostic.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);deadline=time.perf_counter()+120;attempts=[];solution=None;expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids'])
try:
 for index,plan in enumerate(schedule):
  if time.perf_counter()>=deadline:break
  proposal=proposals[plan['proposal_index']];kept=[x for x in event['before_records'] if x['net_id'] not in proposal['release']];core_records=[x for net,i in proposal['core_option_indices'].items() for x in options[int(net)][i]['records']];seed=kept+core_records;assert len(seed)+len(plan['queries'])==len(expected);state=predict(cache.fields,cache.rc,plan['queries'],floors,seed_records=seed,deadline=deadline,spans=spans,penalty=4*(rc.scale//10**11),remaining_cache=cache);file=out/f'branch{index}.json';file.write_text(json.dumps(state)+'\n');attempts.append(dict(index=index,plan=plan,release=proposal['release'],extra_owners=proposal['extra_owners'],state_file=str(file),failure=state['failure']));print('Restore',index,plan['proposal_index'],state['completed_connections'],state['failure'],flush=True)
  if state['failure'] is None:
   assert {x['connection_id'] for x in state['records']}==expected;solution=dict(state,required_connections=len(queries),pending_connection_ids=sorted({q['connection_id'] for q in queries}-expected),released_net_ids=proposal['release'],proposal_index=plan['proposal_index']);break
 cache.finalize()
finally:
 if not cache._closed:cache.abort()
(out/'candidate.json').write_text(json.dumps(solution)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,attempts=attempts,completed=None if solution is None else len(solution['records']),required=len(queries),total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
