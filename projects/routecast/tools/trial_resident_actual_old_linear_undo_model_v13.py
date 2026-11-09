"""Fresh indexed prediction, complete audits and exact frozen-control parity."""
import json,sys,time,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
case=sys.argv[1];assert case in ['xtea','mmc']
if case=='mmc':
 base=R/'experiments/ultraembedded_mmc_actual_old_linear_fraction_cache_workflow_v12_2026-10-10'
 admission=base/'verification.json';proof=json.loads(admission.read_text());assert proof['all_cases_both_complete_arms_authenticated'];control=base/'seed/model/mmc'
else:
 base=R/'experiments/xtea_actual_old_linear_native_handoff_v2_2026-10-09'
 admission=base/'verification.json';proof=json.loads(admission.read_text());assert proof['complete_XTEA_no_fallback_model_seed_and_pending_bytes_equal'];control=base/'model'
assert all(sha(p)==h for p,h in proof['bindings'].items())
old=json.loads((control/'receipt.json').read_text())
assert all(sha(p)==h for sec in ['bindings','files'] for p,h in old[sec].items())
endpoint=next(Path(p) for p in old['bindings'] if p.endswith('/endpoints.json'))
modelscript=R/'tools/run_resident_actual_old_linear_undo_model_v13.py';audits=R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py'
D=R/f'experiments/{case}_actual_old_linear_undo_model_v13_2026-10-10';D.mkdir();model=D/'model'
bindings={**closure([Path(__file__),modelscript,audits]),str(admission):sha(admission),str(endpoint):sha(endpoint),str(control/'receipt.json'):sha(control/'receipt.json')}
undo_admission=R/'experiments/mmc_complete_actual_old_fallback_undo_pair_v1_2026-10-10/verification.json'
u=json.loads(undo_admission.read_text());assert u['all_145_fallback_outputs_and_complete_round_record_replay_equal'] and u['accepted']==115 and u['retained']==30
for section in ['bindings','files']:assert all(sha(p)==h for p,h in u[section].items())
bindings[str(undo_admission)]=sha(undo_admission)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,case=case,scope='Fresh complete indexed model on authenticated development endpoint. Original search, prices and sorted transaction commit unchanged. Actual-old fallback selection uses undo-stack DFS with original candidate order, pruning, visit counts and state-cap semantics; full original independent audit remains required. Full current XML/Fraction physical and event audits paid. Frozen prior control states read only after prediction for exact parity, not decisions. Local model+audit timing only, no conversion/native/full workflow gain or heldout claim.'),indent=2)+'\n')
stages=[];begin=time.perf_counter()
for name,command in [('model',[sys.executable,str(modelscript),str(endpoint),str(model)]),('audits',[sys.executable,str(audits),str(model),case])]:
 tick=time.perf_counter()
 with (D/(name+'.log')).open('w') as f:result=subprocess.run(command,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 stages.append(dict(stage=name,seconds=time.perf_counter()-tick,exit_code=result.returncode))
 (D/'stages.json').write_text(json.dumps(stages,indent=2)+'\n');assert result.returncode==0
local_model_audits_seconds=time.perf_counter()-begin
for filename in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
 a=model/filename;b=control/filename;assert a.read_bytes()==b.read_bytes(),filename
 bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
new=json.loads((model/'receipt.json').read_text())
for a,b in zip(new['rounds'],old['rounds']):
 assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
assert len(new['rounds'])==len(old['rounds'])==2
shared_path=model/'shared_audit_receipt.json';shared=json.loads(shared_path.read_text());assert shared['all_three_complete_audits_pass'] and shared['complete_audit_bodies_AST_preserved']
for sec in ['bindings','files']:
 assert all(sha(p)==h for p,h in new[sec].items())
assert all(sha(p)==h for p,h in shared['bindings'].items())
events=json.loads((model/'verification.json').read_text());assert events['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
bindings[str(shared_path)]=sha(shared_path);bindings[str(model/'verification.json')]=sha(model/'verification.json')
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()},complete_all_states_floors_and_round_event_content_equal_control=True,complete_independent_physical_and_actual_old_events_pass=True,required=events['completed'],fallback_calls=events['fallback_calls'],fallback_accepted=events['fallback_accepted'],local_model_and_audits_seconds=local_model_audits_seconds,model_paid_seconds=new['total_paid_resident_seconds'],historical_control_model_paid_seconds=old['total_paid_resident_seconds'],scope='Complete development state/event parity with independent original XML/Fraction audits. Model and audits subprocesses timed continuously; final parity/archive authentication after local timer. Historical paid-model clock difference descriptive, no randomized/stable/full workflow timing benefit or heldout/silicon claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','files']},indent=2),flush=True)
