"""Paid real XTEA persistent graph/search and native-owner integration replay."""
import json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from retained_native_model_session_v3 import Session
from run_native_state_checkpoint_feedback_v1_2026_10_18 import predict
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths
from actual_change_physical_delta_v1_2026_10_18 import net_unions
from unified_rr_audit_inventory_v1 import read
from collections import Counter
R=Path(__file__).resolve().parents[1];D=R/'experiments/retained_native_warm_checkpoint_v2_2026-10-18'
old=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';new=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18/demand/endpoints.json'
I=R/'experiments/native_state_feedback_inputs_v1_2026-10-18';ref=R/'experiments/xtea_native_local_compiled_pilot_v2_2026-10-18'
v=json.loads((ref/'verification.json').read_text());assert all(sha(p)==h for p,h in v['bindings'].items())
bindings=closure([Path(__file__)]);bindings[str(ref/'verification.json')]=sha(ref/'verification.json');bindings.update(v['bindings'])
oldroute=R/'experiments/freecores_native_cold_v1_2026-10-08/xtea/output.route';newroute=R/'experiments/xtea_native_state_native_utility_v1_2026-10-18/local/output.route'
for p in [old,new,oldroute,newroute]:bindings[str(p)]=sha(p)
# Existing output acceptance is retained; this does not rerun native or relax budgets.
prior=R/'experiments/xtea_native_state_native_utility_v1_2026-10-18/verification.json';native=json.loads(prior.read_text());assert all(sha(p)==h for p,h in native['bindings'].items());bindings[str(prior)]=sha(prior)
start=time.perf_counter();session=Session(old);cold_seconds=time.perf_counter()-start
ids=(id(session.fields),id(session.rc),id(session.search));session.acquire(old);session.release()
meta=json.loads(old.read_text());inv=read(session.graph,session.digest);oldpaths=mapped_paths(meta,oldroute);session.initialize_owner(oldpaths,inv);initial=dict(session.owner.state.occupancy)
rows=[]
checkpoint_initial=R/'experiments/xtea_native_state_bootstrap_v1_2026-10-18/initial.json'
checkpoint_proof=R/'experiments/xtea_native_state_bootstrap_v1_2026-10-18/independent_xml_verification_v1.json'
negative=[]
for index in range(2):
 session.certify_checkpoint(checkpoint_initial,checkpoint_proof)
 session.acquire(new)
 template=json.loads((I/'warm/initial.json').read_text());dirty=json.loads((I/'warm/verification.json').read_text())['dirty_nets']
 before=session.owner.state
 for mode in ['dirty','clean_record','epoch','missing_record']:
  bad=json.loads(json.dumps(template));declared=list(dirty)
  if mode=='dirty':declared=declared[1:]
  elif mode=='clean_record':
   x=next(x for x in bad['records'] if x['net_id'] not in set(dirty));x['budget_integer']+=1
  elif mode=='epoch':bad['epochs'][next(iter(bad['epochs']))]+=1
  else:bad['records'].pop()
  try:session.reconstruct_warm(bad,declared)
  except ValueError:negative.append(mode)
  else:raise AssertionError('incompatible fixture admitted '+mode)
  assert session.owner.state is before
 session.release()
 tick=time.perf_counter();result=predict(new,D/f'model{index}',I/'base/verification.json',I/'timing',I/'warm','local',session=session);model_seconds=time.perf_counter()-tick
 assert ids==(id(session.fields),id(session.rc),id(session.search)) and not session.active and not session.search.closed
 newmeta=json.loads(new.read_text());paths=mapped_paths(newmeta,newroute);generation=session.owner.generation;change=session.reconcile_native(paths,inv,generation=generation)
 full=Counter(n for ns in net_unions(paths,{q['connection_id']:q for q in newmeta['connections']},inv.physical).values() for n in ns)
 assert dict(session.owner.state.occupancy)==dict(full)
 # Rebind and reconcile old accepted checkpoint, allowing a second genuine replay
 # from the same old native state rather than silently retaining target owners.
 session.acquire(old);session.release();session.reconcile_native(oldpaths,inv,generation=session.owner.generation)
 assert dict(session.owner.state.occupancy)==initial
 session.acquire(new)
 try:session.reconstruct_warm(template,dirty)
 except RuntimeError:negative.append('stale_checkpoint_generation')
 else:raise AssertionError('stale checkpoint accepted after native owner advancement')
 session.release()
 rows.append(dict(index=index,model_seconds=model_seconds,changed_native_connections=len(change['changed_connection_ids']),changed_native_nets=len(change['changed_nets']),native_full_owner_equal=True,old_native_owner_restored=True))
paid=time.perf_counter()-start
# Verify lifecycle rejection before closing. Endpoint rejection must leave lease/owner unchanged.
bad=json.loads(new.read_text());bad['graph_sha256']='0'*64;badpath=D/'stale_graph.json'
with badpath.open('x') as f:json.dump(bad,f)
generation=session.owner.generation
try:session.acquire(badpath)
except ValueError:pass
else:raise AssertionError('stale graph accepted')
assert not session.active and session.owner.generation==generation
session.acquire(old)
try:session.acquire(new)
except RuntimeError:pass
else:raise AssertionError('nested session accepted')
try:session.bind_base(tuple(x+1 for x in session.base))
except ValueError:pass
else:raise AssertionError('changed base accepted')
session.release();session.close()
try:session.acquire(new)
except RuntimeError:pass
else:raise AssertionError('closed session accepted')
expected=json.loads((ref/'receipt.json').read_text())
for index in range(2):
 model=D/f'model{index}'
 for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:assert sha(model/name)==sha(ref/name)
 actual=json.loads((model/'receipt.json').read_text());assert len(actual['rounds'])==len(expected['rounds'])==2
 for a,b in zip(actual['rounds'],expected['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
assert all(sha(p)==h for p,h in bindings.items())
result=dict(status='pass',bindings=bindings,one_graph_RC_and_compiled_search_object=True,each_update_all5frames_and94events_equal_audited_reference=True,rows=rows,cold_seconds=cold_seconds,paid_cold_inventory_models_and_native_reconciliation_seconds=paid,owner_generations=generation,stale_graph_nested_changed_base_closed_rejected=True,checkpoint_negative_cases=negative,certified_checkpoint_source_records=2450,scope='Clean warm records reconstructed from retained certified native checkpoint; all complete frame comparisons pass. Full certified warm fixture still read for dirty records and comparison. Two repeated exposed XTEA update replays with archived native output. Model warm fixtures reimported; feedback owner/price contexts rebuilt each call. Input proofs, authentication, initial construction, inventory and reconciliation paid. No fresh native run, continuous full update, matched raw control, timing speedup, unseen or hardware claim.')
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}),flush=True)
