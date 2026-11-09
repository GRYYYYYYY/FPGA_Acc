"""Expanded individually viable scope, whole-NET shared history, compact evidence."""
import sys,json,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from joint_owner_negotiated_dither_v21 import joint_route
out=R/'experiments/misex_net466_expanded_negotiation_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_budget_path_owner_release_v3_2026-10-07';gate=R/'experiments/misex_net466_owner_restoration_viability_v2_2026-10-07/verification.json';gv=json.loads(gate.read_text());assert [x['proposal_index'] for x in gv['cases'] if x['gate_pass']]==[3];ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(gate):sha(gate),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for name in ['event.json','core_options.json','proposals.json','protocol.json','verification.json']:bindings[str(parent/name)]=sha(parent/name)
for asset in [R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute',R/'tools/capped_bound_worker_cpp_v2/main.cpp']:bindings[str(asset)]=sha(asset)
event=json.loads((parent/'event.json').read_text());proposal=json.loads((parent/'proposals.json').read_text())[3];options={int(n):ops for n,ops in json.loads((parent/'core_options.json').read_text()).items()};protected=set(json.loads((parent/'protocol.json').read_text())['protected_connection_ids']);seed=[x for x in event['before_records'] if x['net_id'] not in proposal['release'] or x['connection_id'] in protected]+[x for n,i in proposal['core_option_indices'].items() for x in options[int(n)][i]['records']];seedids={x['connection_id'] for x in seed};assert len(seedids)==len(seed);expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids']);assert len(expected)==2172;(out/'event.json').write_text(json.dumps(event)+'\n');(out/'seed.json').write_text(json.dumps(seed)+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);groups=defaultdict(list)
for q in queries:
 if q['connection_id'] in expected-seedids:groups[q['net_id']].append(q)
floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,groups=groups,proposal_index=3,release=proposal['release'],protected_connection_ids=sorted(protected),round_limit=32,shared_search_seconds=120,history='NET/node SHA weight8..15; spans plus accumulated overuse',scope='Each wholeNET independently grows against same exact immutable kept/core/protectedseed; merge ALL groups only at zero capacity overuse. Compact archived state records contain new records only; seed.json must be materialized for physical audits. Original budgets/all2172CID remain mandatory; post-outcome exploration, no native/heldout/workflow gain.'),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);start=time.perf_counter()
def observe(branch,states,merged):
 folder=out/f"round{branch['index']}";folder.mkdir();(folder/'branch.json').write_text(json.dumps(branch)+'\n')
 for net,state in states.items():
  assert all(next(x for x in state['records'] if x['connection_id']==rec['connection_id'])==rec for rec in seed)
  compact=dict(state,records=[x for x in state['records'] if x['connection_id'] not in seedids],seed_file=str(out/'seed.json'));(folder/f'net{net}.json').write_text(json.dumps(compact)+'\n')
 print('ROUND',branch['index'],branch['status'],branch.get('conflict_count'),flush=True)
try:
 result=joint_route(cache.fields,cache.rc,dict(groups),floors,seed,spans,4*(rc.scale//10**11),len(queries),remaining_cache=cache,max_joint_nodes=32,deadline=start+120,observer=observe,frontier='negotiated_history');cache.finalize()
finally:
 if not cache._closed:cache.abort()
candidate=result['solution']
if candidate is not None:assert {x['connection_id'] for x in candidate['records']}==expected;candidate['pending_connection_ids']=sorted({q['connection_id'] for q in queries}-expected)
(out/'candidate.json').write_text(json.dumps(candidate)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,status=result['status'],branches=result['branches'],completed=None if candidate is None else len(candidate['records']),required=len(queries),total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
