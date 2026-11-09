"""Verified rollback-domain local repair; all original requests remain mandatory."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from tree_floor_pareto_affected_seed_v13 import predict
out=R/'experiments/misex_net466_local_owner_repair_v1_2026-10-07';out.mkdir();begin=time.perf_counter();domains=R/'experiments/misex_net466_restored_owner_rollback_domains_v1_2026-10-07';vp=domains/'verification.json';dv=json.loads(vp.read_text());assert dv['immutable_seed_and_complete_mutable_net_enumeration_pass'];rp=domains/'receipt.json';assert sha(rp)==dv['bindings'][str(rp)];dr=json.loads(rp.read_text());parent=R/'experiments/misex_net466_budget_path_owner_joint_v3_2026-10-07';pp=R/'experiments/misex_net466_budget_path_owner_release_v3_2026-10-07';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(rp):sha(rp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for asset in [parent/'receipt.json',parent/'protocol.json',pp/'event.json',pp/'core_options.json',pp/'proposals.json']:
 bindings[str(asset)]=sha(asset);assert dv['bindings'][str(asset)]==bindings[str(asset)] if str(asset) in dv['bindings'] else True
for row in dr['rows']:bindings[row['state_file']]=sha(row['state_file']);assert bindings[row['state_file']]==dv['bindings'][row['state_file']]
for asset in [R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute',R/'tools/capped_bound_worker_cpp_v2/main.cpp']:bindings[str(asset)]=sha(asset)
event=json.loads((pp/'event.json').read_text());prior=json.loads((parent/'receipt.json').read_text());options={int(n):ops for n,ops in json.loads((pp/'core_options.json').read_text()).items()};proposals=json.loads((pp/'proposals.json').read_text());protected=set(json.loads((parent/'protocol.json').read_text())['protected_original_connection_ids']);graph,digest,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids']);assert len(expected)==2172;plans=[];seeds={}
for row in dr['rows']:
 a=prior['attempts'][row['branch']];state=json.loads(Path(row['state_file']).read_text());records={x['connection_id']:x for x in state['records']};proposal=proposals[a['plan']['proposal_index']];initial=[x for x in event['before_records'] if x['net_id'] not in proposal['release'] or x['connection_id'] in protected]+[x for n,i in proposal['core_option_indices'].items() for x in options[int(n)][i]['records']];immutable={x['connection_id']:x for x in initial};assert all(records[c]==x for c,x in immutable.items());failednet=row['query']['net_id'];failedcid=row['query']['connection_id'];failed_mutable={c for c,x in records.items() if x['net_id']==failednet and c not in immutable}
 for rollback in row['ranked_feasible_rollback_nets'][:2]:
  check=next(x for x in row['checks'] if x['rollback_net']==rollback);removed=failed_mutable|set(check['removed_connection_ids']);seed=[x for c,x in records.items() if c not in removed];assert not removed.intersection(immutable);groups=defaultdict(list)
  for cid in sorted(expected-{x['connection_id'] for x in seed}):groups[qm[cid]['net_id']].append(qm[cid])
  order=[failednet,rollback]+[n for n in a['plan']['net_order'] if n in groups and n not in [failednet,rollback]];assert len(order)==len(set(order)) and set(order)==set(groups)
  for variant in range(3):
   qs=[]
   for n in order:
    g=groups[n];g=sorted(g,key=lambda q:q['connection_id'] if variant==0 else -q['connection_id'] if variant==1 else (-floors[q['source'],q['sink']],q['connection_id']))
    if n==failednet:g=sorted(g,key=lambda q:q['connection_id']!=failedcid)
    qs.extend(g)
   index=len(plans);plans.append(dict(index=index,source_branch=row['branch'],rollback_net=rollback,failed_net=failednet,query_variant=variant,removed_connection_ids=sorted(removed),net_order=order,queries=qs));seeds[index]=seed
# Interleave variants so each source/rollback gets an attempt before spending budget on query-order repeats.
schedule=sorted(plans,key=lambda p:(p['query_variant'],p['source_branch'],p['index']));(out/'event.json').write_text(json.dumps(event)+'\n');(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,schedule=schedule,shared_search_seconds=120,max_labels=10000,policy='Top2 independently feasible single-owner rollback domains per failed state; remove ALL mutable records of failedNET and blockerNET, preserve exact initial kept/core/protectedseed and every other retained record. Failed query first, complete failedNET then blockerNET then every remaining original request. Three CID/floor order variants, interleaved. No partialdropcommit; candidate only when ALL2172CID restored, original2449partition preserved.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);deadline=time.perf_counter()+120;attempts=[];solution=None
try:
 for sequence,plan in enumerate(schedule):
  if time.perf_counter()>=deadline:break
  state=predict(cache.fields,cache.rc,plan['queries'],floors,seed_records=seeds[plan['index']],deadline=deadline,spans=spans,penalty=4*(rc.scale//10**11),remaining_cache=cache);file=out/f'repair{sequence}.json';file.write_text(json.dumps(state)+'\n');attempts.append(dict(sequence=sequence,plan=plan,state_file=str(file),failure=state['failure']));print('LOCAL REPAIR',sequence,plan['source_branch'],plan['rollback_net'],state['completed_connections'],state['failure'],flush=True)
  if state['failure'] is None:
   assert {x['connection_id'] for x in state['records']}==expected;solution=dict(state,required_connections=len(queries),pending_connection_ids=sorted(set(qm)-expected),repair_plan=plan);break
 cache.finalize()
finally:
 if not cache._closed:cache.abort()
(out/'candidate.json').write_text(json.dumps(solution)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,attempts=attempts,completed=None if solution is None else len(solution['records']),required=len(queries),total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
