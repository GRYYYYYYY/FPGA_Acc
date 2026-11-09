"""Paid full MMC component execution and audited-reference semantic parity."""
import json,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_sparse_round_feedback_v1_2026-10-18'
ref=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/model'
script=R/'tools/run_mmc_native_sparse_round_feedback_v1_2026_10_18.py'
bindings=closure([Path(__file__),script])
for name in ['initial.json','sketch.json','events.json']:
 p=R/'experiments/mmc_native_cached_feedback_audits_v1_2026-10-18'/name
 v=json.loads(p.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
expected=json.loads((ref/'receipt.json').read_text());bindings[str(ref/'receipt.json')]=sha(ref/'receipt.json');bindings.update(expected['files'])
assert all(sha(p)==h for p,h in bindings.items())
I=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18'
cmd=[sys.executable,str(script),str(R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json'),str(O/'model'),str(I/'base/verification.json'),str(I/'timing'),str(I/'warm'),'local']
with (O/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,command=cmd,scope='Full paid single model component against historical audited dense reference; unpaired timing diagnostic only; not continuous frontend/floor/audit/native/canonical workflow.'),f,indent=2)
t=time.perf_counter()
with (O/'model.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
with (O/'terminal.json').open('x') as f:json.dump(dict(exit_status=code,wall_seconds=time.perf_counter()-t),f)
assert code==0
model=O/'model';actual=json.loads((model/'receipt.json').read_text())
frames={name:sha(model/name)==sha(ref/name) for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']};assert all(frames.values())
assert len(actual['rounds'])==len(expected['rounds'])==2
for a,b in zip(actual['rounds'],expected['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
assert all(sha(p)==h for p,h in bindings.items())
metrics=['total_paid_resident_seconds','model_setup_seconds','initial_seconds','feedback_seconds','cpp_prepare_seconds','search_seconds','occupancy_context_seconds','fallback_seconds','ledger_check_seconds']
result=dict(status='pass',bindings=bindings,all_five_full_frames_byte_identical=frames,all108_events_equal=True,audit_scope='Semantic equality to bound independently XML/Fraction audited dense outputs; no new independent audit implementation.',timers={k:actual[k] for k in metrics},historical_dense_timers={k:expected[k] for k in metrics},timing_scope='Unpaired diagnostic; includes initial dense prices and all model setup. Not full end-to-end benefit or cross-placement persistence.',native_rerun=False,default_promoted=False,old_floor_certificate_scope_unchanged=True)
with (O/'verification.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}),flush=True)
