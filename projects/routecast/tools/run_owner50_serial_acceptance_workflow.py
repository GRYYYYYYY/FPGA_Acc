"""Single serial prepared-input full12 workflow; no cross-run timer stitching."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/owner50_serial_acceptance_workflow_2026-10-07';TAG='owner50_serial_2026-10-07'
FLOOR=TAG+'_floor';PRED=TAG+'_predictor';FALLBACK=TAG+'_fallback';COLD=TAG+'_cold'
def clone(src,name,replacements):
 s=(ROOT/'tools'/src).read_text()
 for a,b in replacements:s=s.replace(a,b)
 f=ROOT/'tools'/name;assert not f.exists();f.write_text(s);return str(f)
def initialize():
 OUT.mkdir();tools={}
 for prefix in ('prepare','verify'):
  tools['floor_'+prefix]=clone(prefix+'_mux_critical_release_floor_only.py',prefix+'_'+TAG+'_floor.py',[('mux_critical_release_floor_only_2026-10-07',FLOOR)])
 tools['predictor']=clone('trial_owner50_floor_only_consumer.py','trial_'+TAG+'_predictor.py',[('mux_owner50_floor_only_consumer_2026-10-07',PRED),('mux_critical_release_floor_only_2026-10-07',FLOOR)])
 tools['predictor_verify']=clone('verify_owner50_floor_only_consumer.py','verify_'+TAG+'_predictor.py',[('mux_owner50_floor_only_consumer_2026-10-07',PRED),('mux_critical_release_floor_only_2026-10-07',FLOOR)])
 for prefix in ('trial','verify'):
  tools['fallback_'+prefix]=clone(prefix+'_owner50_ten_case_fallback_cost.py',prefix+'_'+TAG+'_fallback.py',[('mux_owner50_ten_case_fallback_cost_2026-10-07',FALLBACK),('mux_owner50_floor_only_consumer_2026-10-07',PRED)])
  tools['cold_'+prefix]=clone(prefix+'_mux_joint_qor_cost_cold_reference.py',prefix+'_'+TAG+'_cold.py',[('mux_joint_qor_cost_cold_reference_2026-10-07',COLD)])
 gates=[]
 for i in (2,3):
  label=TAG+f'_gate_w8m{i}'
  files={}
  for prefix in ('trial','verify'):
   files[prefix]=clone(f'{prefix}_mux_native_joint_50ps_w8m{i}_quality_gate.py',f'{prefix}_{label}.py',[(f'mux_native_joint_50ps_w8m{i}_quality_gate_2026-10-07',label),('mux_owner_wire_50ps_development_2026-10-07',PRED)])
  gates.append(dict(index=i,output=label,**files))
 sources=[Path(__file__),*[Path(f) for f in tools.values()],*[Path(g[k]) for g in gates for k in ('trial','verify')]]
 (OUT/'protocol.json').write_text(json.dumps(dict(tools=tools,gates=gates,sources={str(f):sha(f) for f in sources},joint_binary_sha256=sha(ROOT/'build/native_joint_qor_gate_2026-10-07/gate_vpr'),scope='Single serial FULL12 prepared-input development50ps workflow: fresh floor-only preparation+independent proof; fresh actual predictor all12+exact complete consumer parity; archived six case proofs rebound ONLY through exact normalized result equality; fresh native joint coldreference/candidate gate, selected canonical and independent route/wire checks; selected candidate context/import; all10 fresh nativecold fallback+canonical/physical/import+independent snapshots. ALL clocks from this run. Fresh full12 cold baseline executes AFTER workflow with same prepared input scope and independent proof. Upstream allfanin floors/originalSTA/RR-endpoint conversion/frontend/initialseedroute/build excluded reusable inputs and additional, NOT raw-input complete end-to-end. Process-per-stage conservative current implementation; not theoretical minimum, heldout or stable paired speedup. Fixed reproducibility fixture expects2 modelPASS after exact parity, not generic deployment policy.'),indent=2)+'\n');print('Full12 serial workflow protocol frozen')
def run():
 p=json.loads((OUT/'protocol.json').read_text());assert all(sha(f)==h for f,h in p['sources'].items());assert p['joint_binary_sha256']==sha(ROOT/'build/native_joint_qor_gate_2026-10-07/gate_vpr');rows=[];start=time.perf_counter();t=p['tools']
 def checkpoint():
  (OUT/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(OUT/'protocol.json'),stages=rows,complete=False),indent=2)+'\n')
 def stage(name,tool):
  begin=time.perf_counter()
  with (OUT/(name+'.log')).open('w') as stream:code=subprocess.run([sys.executable,tool],stdout=stream,stderr=subprocess.STDOUT,timeout=600).returncode
  rows.append(dict(name=name,seconds=time.perf_counter()-begin,exit_code=code));checkpoint();assert code==0;print(name,rows[-1]['seconds'],flush=True)
 stage('floor_preparation',t['floor_prepare']);stage('floor_independent_proof',t['floor_verify']);stage('full12_prediction',t['predictor']);stage('full12_prediction_parity',t['predictor_verify'])
 pred=ROOT/'experiments'/PRED;vr=json.loads((pred/'verification.json').read_text());assert vr['receipt_sha256']==sha(pred/'receipt.json');pr=json.loads((pred/'receipt.json').read_text());passes={(x['width'],x['index']) for x in pr['rows'] if x['status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING'};assert passes=={(8,2),(8,3)}
 begin=time.perf_counter()
 for i in (2,3):
  old=ROOT/f'experiments/mux_owner_wire_50ps_development_2026-10-07/w8_m{i}';work=pred/f'w8_m{i}';a=json.loads((old/'result.json').read_text());b=json.loads((work/'result.json').read_text());a.pop('initial_floor_seed_sha256');b.pop('initial_floor_seed_sha256');assert a==b
  oldproof=json.loads((old/'native_input_verification.json').read_text());assert oldproof['result_sha256']==sha(old/'result.json')
  for name,h in oldproof['audits'].items():assert sha(old/(name+'.json'))==h
  (work/'native_input_verification.json').write_text(json.dumps(dict(result_sha256=sha(work/'result.json'),protocol_sha256=sha(pred/'protocol.json'),whole_consumer_parity_sha256=sha(pred/'verification.json'),archived_native_input_sha256=sha(old/'native_input_verification.json'),archived_audits=oldproof['audits'],scope='Archived six proofs rebound via exact whole nested result parity except validated preparation digest; no native content reuse, new joint native execution follows.'),indent=2)+'\n')
 rows.append(dict(name='proof_binding',seconds=time.perf_counter()-begin,exit_code=0));checkpoint()
 from persistent_rc_context import PersistentRCContext
 from native_route_ledger_import import import_native_ledger
 admitted=[]
 for g in p['gates']:
  i=g['index'];stage(f'w8_m{i}_native_joint_gate',g['trial']);stage(f'w8_m{i}_native_independent_proof',g['verify']);base=ROOT/'experiments'/g['output'];r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')
  rr=r['rows'][0]['reload'];assert rr['mismatches']==rr['fixups']==0;route=next(Path(f) for f in rr['files'] if f.endswith('/design.route'));assert sha(route)==rr['files'][str(route)];spec=json.loads((base/'protocol.json').read_text())['cases'][0]
  begin=time.perf_counter();ctx=PersistentRCContext(spec['target']);state=import_native_ledger(ctx,route);assert len(state.records)==466;snapshot=OUT/f'w8_m{i}_accepted_state.json';snapshot.write_text(json.dumps(dict(revision=1,records=[state.records[k] for k in sorted(state.records)],ledger=dict(state.ledger),endpoint_metadata=ctx.endpoint_metadata,scale=ctx.rc.scale),indent=2)+'\n');admitted.append(dict(width=8,index=i,selected=v['rows'][0]['selected'],selected_route=str(route),selected_route_sha256=sha(route),snapshot_sha256=sha(snapshot),metrics=v['rows'][0]));rows.append(dict(name=f'w8_m{i}_selected_import',seconds=time.perf_counter()-begin,exit_code=0));checkpoint()
 stage('all10_native_fallback',t['fallback_trial']);stage('all10_fallback_independent_proof',t['fallback_verify']);workflow_seconds=time.perf_counter()-start
 stage('fresh_full12_cold_baseline',t['cold_trial']);stage('fresh_full12_cold_independent_proof',t['cold_verify'])
 (OUT/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(OUT/'protocol.json'),stages=rows,workflow_wall_seconds=workflow_seconds,candidates=admitted,complete=True,scope=p['scope']),indent=2)+'\n');print('Serial full12 workflow complete',workflow_seconds,flush=True)
if __name__=='__main__':
 if sys.argv[1:]==['--initialize']:initialize()
 else:run()
