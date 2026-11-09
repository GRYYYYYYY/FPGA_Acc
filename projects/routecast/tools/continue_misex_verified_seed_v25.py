"""Post-outcome sequential continuation from independently validated local joint seed."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_worker_cache_v7 import RemainingDelayCache
from tree_floor_pareto_affected_seed_v13 import predict
parent=R/'experiments/misex_net415_extra_owner_joint_v1_2026-10-07';out=R/'experiments/misex_verified_seed_continuation_v25_2026-10-07';out.mkdir();bindings=closure([Path(__file__)])
for name in ('branch_verification_dedup.json','bound_verification.json'):
 p=parent/name;proof=json.loads(p.read_text());assert all(sha(k)==v for k,v in proof['bindings'].items());bindings[str(p)]=sha(p)
seedfile=parent/'candidate.json';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json'
for p in (seedfile,ep,fp,R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute',R/'tools/capped_bound_worker_cpp_v2/main.cpp'):bindings[str(p)]=sha(p)
bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,deadline_seconds=120,policy='Sequential remaining NET/CID, max1ns or ceil1.5floor, penalty0.04ns/newCHANspan, labels10000, original immutable model FIFO256 worker cache; validated seed import paid.',scope='Post-outcome snapshot continuation; not from-empty, native, heldout or end-to-end gain evidence.'),indent=2)+'\n');begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);seed=json.loads(seedfile.read_text());done={x['connection_id'] for x in seed['records']};assert len(done)==2068;pending=sorted([q for q in queries if q['connection_id'] not in done],key=lambda q:(q['net_id'],q['connection_id']));assert len(pending)==381;floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);start=time.perf_counter()
try:
 state=predict(cache.fields,cache.rc,pending,floors,seed_records=seed['records'],deadline=start+120,spans=spans,penalty=4*(rc.scale//10**11),max_labels=10000,remaining_cache=cache);cache.finalize()
finally:
 if not cache._closed:cache.abort()
records={x['connection_id']:x for x in state['records']};assert all(records[x['connection_id']]==x for x in seed['records']);state['required_connections']=len(queries);state['pending_connection_ids']=sorted({q['connection_id'] for q in queries}-records.keys());state['status']='COMPLETE_DIAGNOSTIC' if not state['pending_connection_ids'] else 'INCOMPLETE_NOT_PUBLISHABLE';(out/'candidate.json').write_text(json.dumps(state)+'\n');(out/'cache_receipt.json').write_text(json.dumps(cache.summary(),indent=2)+'\n');assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,completed=state['completed_connections'],required=len(queries),failure=state['failure'],total_component_seconds=time.perf_counter()-begin,search_and_finalize_seconds=time.perf_counter()-start,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n');print('CONTINUATION',state['completed_connections'],len(queries),state['failure'],flush=True)
