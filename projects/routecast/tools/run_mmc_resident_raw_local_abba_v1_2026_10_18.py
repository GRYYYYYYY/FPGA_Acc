"""Balanced same-source resident MMC raw/local component comparison."""
import json,time,sys,contextlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from persistent_raw_compiled_session_v1 import Session as RawSession
from mmc_native_dirty_recipe_model_session_v1 import Session as LocalSession
from run_native_state_dirty_recipe_feedback_v1_2026_10_18 import predict
from prepare_native_dirty_transition_recipe_v1 import prepare
from unified_rr_audit_inventory_v1 import read
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_resident_raw_local_abba_v1_2026-10-18'
contract=json.loads((D/'protocol.json').read_text());assert contract['order']==['raw','local','local','raw']
bindings={**closure([Path(__file__)]),str(D/'protocol.json'):sha(D/'protocol.json')}
for name in ['mmc_persistent_raw_compiled_v1_2026-10-18','mmc_native_dirty_transition_recipe_v1_2026-10-18']:
 p=R/'experiments'/name/'verification.json';v=json.loads(p.read_text());assert v['status']=='pass' and all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
geo=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());old=Path(geo['previous_endpoint']);route=Path(geo['previous_native_route']);new=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json'
I=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18';source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';rawref=R/'experiments/mmc_native_raw_control_v1_2026-10-18';localref=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/model'
setup_start=time.perf_counter();raw=RawSession(old,route);raw_setup=time.perf_counter()-setup_start;print('SETUP RAW DONE',raw_setup,flush=True)
setup_start=time.perf_counter();recipe=D/'dirty_recipe.json';production=prepare(I/'warm',source/'initial.json',recipe)
local=LocalSession(old);local.recipe=recipe;local.acquire(old);local.release();inventory=read(local.graph,local.digest);paths=mapped_paths(json.loads(old.read_text()),route);local.initialize_owner(paths,inventory);local.certify_checkpoint(source/'initial.json',source/'independent_xml_verification_v1.json');local_setup=time.perf_counter()-setup_start;print('SETUP LOCAL DONE',local_setup,flush=True)
raw_ids=(id(raw.fields),id(raw.rc),id(raw.nativerows));local_ids=(id(local.fields),id(local.rc),id(local.search));owner=local.owner.state;raw_state=raw.state
setup=dict(raw_cold_seconds=raw_setup,local_cold_inventory_source_certificate_recipe_seconds=local_setup,local_recipe_seconds_nested=production['production_seconds'],global_oldF_production_measured=False)
with (D/'setup.json').open('x') as f:json.dump(setup,f,indent=2)
rows=[]
for index,arm in enumerate(contract['order']):
 output=D/f'call{index}_{arm}';tick=time.perf_counter()
 with (D/f'call{index}_{arm}.log').open('x') as log,contextlib.redirect_stdout(log):
  if arm=='raw':result=raw.predict(new,output,generation=0)
  else:result=predict(new,output,I/'base/verification.json',I/'timing',I/'warm','local',session=local)
 elapsed=time.perf_counter()-tick
 rows.append(dict(index=index,arm=arm,complete_call_seconds=elapsed,output=str(output)))
 with (D/'rows.jsonl').open('a') as f:f.write(json.dumps(rows[-1])+'\n')
 assert raw_ids==(id(raw.fields),id(raw.rc),id(raw.nativerows)) and local_ids==(id(local.fields),id(local.rc),id(local.search))
 assert local.owner.state is owner and local.owner.generation==0 and raw.state is raw_state and raw.generation==0
 print('CALL DONE',index,arm,elapsed,flush=True)
# Everything below is reference validation outside production clocks.
expected_raw=json.loads((rawref/'receipt.json').read_text());expected_local=json.loads((localref/'receipt.json').read_text())
for row in rows:
 output=Path(row['output'])
 if row['arm']=='raw':
  assert sha(output/'initial.json')==sha(rawref/'initial.json')
  assert len(list((output/'certificates').glob('source_*.json')))==54
  for spec in expected_raw['certificates']:
   p=Path(spec['path']);assert sha(p)==spec['sha256'];assert json.loads((output/'certificates'/p.name).read_text())==json.loads(p.read_text())
 else:
  for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:assert sha(output/name)==sha(localref/name)
  actual=json.loads((output/'receipt.json').read_text());assert len(actual['rounds'])==len(expected_local['rounds'])==2
  for a,b in zip(actual['rounds'],expected_local['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
raw.close();local.close()
pairs=[]
for ri,li in contract['pairs']:
 r=rows[ri];l=rows[li];assert r['arm']=='raw' and l['arm']=='local'
 pairs.append(dict(raw_index=ri,local_index=li,raw_seconds=r['complete_call_seconds'],local_seconds=l['complete_call_seconds'],local_over_raw=l['complete_call_seconds']/r['complete_call_seconds'],passes_5pct_latency_gate=l['complete_call_seconds']<=.95*r['complete_call_seconds']))
assert all(sha(p)==h for p,h in bindings.items())
for row in rows:
 p=Path(row['output'])/'receipt.json';bindings[str(p)]=sha(p)
result=dict(status='pass',bindings=bindings,order=contract['order'],rows=rows,setup=setup,pairs=pairs,all_full_frame_and_certificate_or_event_reference_checks_pass=True,source_contexts_and_generation_unchanged=True,local_resident_latency_gate_pass=all(p['passes_5pct_latency_gate'] for p in pairs),local_wire_nonregression_pass=False,full_end_to_end_gain_proven=False,default_promoted=False,scope='Balanced4calls on one exposed same-source speculative MMC update, resident model component only. Actual native physical/canonical outcome unchanged from bound archived outputs. Cold contexts/recipe/source certificate measured separately; no new global old-floor production, native/full workflow clock, strict heldout, distinct accepted placement sequence, stable population or hardware claim.')
with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}),flush=True)
