"""Paid real XTEA persistent graph/search and native-owner integration replay."""
import json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from mmc_native_dirty_recipe_model_session_v1 import Session
from prepare_native_dirty_transition_recipe_v1 import prepare
from unittest.mock import patch
from run_native_state_dirty_recipe_feedback_v1_2026_10_18 import predict
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths
from actual_change_physical_delta_v1_2026_10_18 import net_unions
from unified_rr_audit_inventory_v1 import read
from collections import Counter
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_dirty_transition_recipe_v1_2026-10-18'
old=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';new=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json'
I=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18';ref=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/model'
audit_path=R/'experiments/mmc_native_cached_feedback_audits_v1_2026-10-18/verification.json';v=json.loads(audit_path.read_text());assert v['all_three_frame_and_complete_event_audits_pass'] and not v['old_all_floor_independent_minimum_dual_certification'];assert all(sha(p)==h for p,h in v['bindings'].items())
bindings=closure([Path(__file__)]);bindings[str(audit_path)]=sha(audit_path);bindings.update(v['bindings'])
oldroute=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/native/mmc/output.route';newroute=R/'experiments/mmc_native_seed_utility_pilot_v1_2026-10-18/local/output.route'
for p in [old,new,oldroute,newroute]:bindings[str(p)]=sha(p)
# Existing output acceptance is retained; this does not rerun native or relax budgets.
prior=R/'experiments/mmc_recovered_native_cohort_v1_2026-10-18/verification.json';native=json.loads(prior.read_text());assert all(sha(p)==h for p,h in native['bindings'].items());bindings[str(prior)]=sha(prior)
checkpoint_initial=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json'
checkpoint_proof=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json'
source_proof=json.loads(checkpoint_proof.read_text());assert source_proof['all_native_paths_exact'] and not source_proof['all_old_per_design_minima_independently_recertified']
recipe=D/'dirty_recipe.json';production=prepare(I/'warm',checkpoint_initial,recipe)
bindings[str(recipe)]=sha(recipe);bindings[str(recipe.with_suffix('.proof.json'))]=sha(recipe.with_suffix('.proof.json'))
start=time.perf_counter();session=Session(old);session.recipe=recipe;cold_seconds=time.perf_counter()-start
ids=(id(session.fields),id(session.rc),id(session.search));session.acquire(old);session.release()
meta=json.loads(old.read_text());inv=read(session.graph,session.digest);oldpaths=mapped_paths(meta,oldroute);session.initialize_owner(oldpaths,inv);initial=dict(session.owner.state.occupancy)
rows=[];negative=[];blocked_reads=0
original_read=Path.read_text
forbidden=(I/'warm/initial.json').resolve()
def guarded_read(path,*args,**kwargs):
 global blocked_reads
 if path.resolve()==forbidden:
  blocked_reads+=1;raise AssertionError('full warm initial parsing forbidden during model')
 return original_read(path,*args,**kwargs)
for index in range(2):
 session.certify_checkpoint(checkpoint_initial,checkpoint_proof)
 session.acquire(new);payload=json.loads(recipe.read_text());dirty=payload['dirty_nets'];before=session.owner.state
 for mode in ['missing_dirty','extra_clean','dirty_closure','source_hash','changed_delay']:
  bad=json.loads(json.dumps(payload))
  if mode=='missing_dirty':bad['dirty_records'].pop()
  elif mode=='extra_clean':bad['dirty_records'].append(json.loads(next(text for cid,text in session.checkpoint.records.items() if session.current_queries[cid]['net_id'] not in set(dirty))))
  elif mode=='dirty_closure':bad['dirty_nets']=bad['dirty_nets'][1:]
  elif mode=='source_hash':bad['source_initial_sha256']='0'*64
  else:bad['dirty_records'][0]['answer']['delay']+=1
  try:session.checkpoint._build(bad,dirty)
  except ValueError:negative.append(mode)
  else:raise AssertionError('bad dirty recipe admitted '+mode)
  assert session.owner.state is before
 session.release();tick=time.perf_counter()
 with patch.object(Path,'read_text',guarded_read):
  result=predict(new,D/f'model{index}',I/'base/verification.json',I/'timing',I/'warm','local',session=session)
 model_seconds=time.perf_counter()-tick
 assert ids==(id(session.fields),id(session.rc),id(session.search)) and not session.active and not session.search.closed
 newmeta=json.loads(new.read_text());paths=mapped_paths(newmeta,newroute);generation=session.owner.generation;change=session.reconcile_native(paths,inv,generation=generation)
 full=Counter(n for ns in net_unions(paths,{q['connection_id']:q for q in newmeta['connections']},inv.physical).values() for n in ns)
 assert dict(session.owner.state.occupancy)==dict(full)
 # Rebind and reconcile old accepted checkpoint, allowing a second genuine replay
 # from the same old native state rather than silently retaining target owners.
 session.acquire(old);session.release();session.reconcile_native(oldpaths,inv,generation=session.owner.generation)
 assert dict(session.owner.state.occupancy)==initial
 session.acquire(new)
 try:session.checkpoint._build(payload,dirty)
 except RuntimeError:negative.append('stale_source_generation')
 else:raise AssertionError('stale checkpoint admitted')
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
result=dict(status='pass',bindings=bindings,one_graph_RC_and_compiled_search_object=True,each_update_all5frames_and108events_equal_audited_reference=True,rows=rows,cold_seconds=cold_seconds,paid_cold_inventory_models_and_native_reconciliation_seconds=paid,owner_generations=generation,stale_graph_nested_changed_base_closed_rejected=True,recipe_production=production,no_full_warm_initial_read_text_during_model=blocked_reads==0,negative_recipe_cases=negative,scope='Dirty recipe transport: clean records reconstructed from retained certified checkpoint, full warm initial never parsed during model. Dependency hashes still read full bound files and source checkpoint initially parsed. Two repeated exposed MMC update replays; old all-floor minimum dual certificate scope remains false with archived native output. Model warm fixtures reimported; feedback owner/price contexts rebuilt each call. Input proofs, authentication, initial construction, inventory and reconciliation paid. No fresh native run, continuous full update, matched raw control, timing speedup, unseen or hardware claim.')
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','recipe_production']}),flush=True)
