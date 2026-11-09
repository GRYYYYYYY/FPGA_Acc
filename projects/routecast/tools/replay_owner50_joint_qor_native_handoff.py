"""All12 native joint-quality admission/content handoff replay, not live timing."""
import json,re,time
from pathlib import Path
from fractions import Fraction
from native_joint_qor_admission import decide
from native_route_ledger_import import import_native_ledger
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/owner50_joint_qor_native_handoff_2026-10-07'
COLD=ROOT/'experiments/mux_joint_qor_cost_cold_reference_2026-10-07'
PRED=ROOT/'experiments/mux_owner_wire_50ps_development_2026-10-07'

def initialize():
 OUT.mkdir()
 files=[Path(__file__),ROOT/'tools/native_joint_qor_admission.py',ROOT/'tools/native_route_ledger_import.py',ROOT/'tools/persistent_rc_context.py']
 (OUT/'protocol.json').write_text(json.dumps(dict(sources={str(f):sha(f) for f in files},admission_contract_sha256=sha(ROOT/'experiments/native_joint_qor_admission_contract_2026-10-07/verification.json'),prediction_receipt_sha256=sha(PRED/'receipt.json'),prediction_protocol_sha256=sha(PRED/'protocol.json'),frozen_cases_sha256=sha(ROOT/'experiments/mux_budget_move_cohort_2026-10-06/protocol.json'),policy='Chosen development50ps policy, all12 cases. No complete/modelPASS/native proof => cold reference. Native candidate CPD and perNET-union wire must both not exceed same-target cold. CPD equality allowed; strict wire tolerance zero. Fresh cold accepted snapshots required and authenticated; admitted candidates archived freshly proven development content. No live prediction or new candidate native execution in this replay. Import selected original canonical route into bound target context; serialize new revision1 accepted snapshot. No end-to-end speed claim, concurrent/durable publication or heldout claim.'),indent=2)+'\n')

def run():
 p=json.loads((OUT/'protocol.json').read_text());assert all(sha(f)==h for f,h in p['sources'].items());assert sha(PRED/'receipt.json')==p['prediction_receipt_sha256']
 cp=json.loads((COLD/'protocol.json').read_text());cr=json.loads((COLD/'receipt.json').read_text());cv=json.loads((COLD/'verification.json').read_text());assert cv['receipt_sha256']==sha(COLD/'receipt.json');assert len(cr['rows'])==len(cp['cases'])==12
 pr=json.loads((PRED/'receipt.json').read_text());bindings={str(COLD/'receipt.json'):sha(COLD/'receipt.json'),str(COLD/'verification.json'):sha(COLD/'verification.json')};rows=[]
 def read(f):bindings[str(f)]=sha(f);return json.loads(f.read_text())
 def wire(log):return int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1])
 for case,cold in zip(cp['cases'],cr['rows']):
  w,i=case['width'],case['index'];assert cold['complete'] and cold['error'] is None and (cold['width'],cold['index'])==(w,i)
  rr=cold['rounds'][0];reload=rr['reload'];assert reload['mismatches']==reload['fixups']==0
  route=next(Path(f) for f in reload['files'] if f.endswith('/design.route'));log=next(Path(f) for f in reload['files'] if f.endswith('/reload.log'))
  assert all(sha(f)==h for f,h in reload['files'].items());reference=dict(cpd_ns=str(reload['cpd_ns']),wirelength=wire(log));candidate=None;candidate_route=None
  pred=next(x for x in pr['rows'] if (x['width'],x['index'])==(w,i))
  if pred['status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING':
   own=ROOT/f'experiments/mux_owner_wire_50ps_w{w}m{i}_candidate_canonical_2026-10-07';gate=ROOT/f'experiments/mux_owner_wire_50ps_w{w}m{i}_quality_gate_2026-10-07'
   v=read(own/'verification.json');receipt=read(own/'receipt.json');gv=read(gate/'verification.json');gr=read(gate/'receipt.json');assert v['receipt_sha256']==sha(own/'receipt.json') and gv['receipt_sha256']==sha(gate/'receipt.json') and v['gate_verification_sha256']==sha(gate/'verification.json')
   assert v['connections']=={8:466,16:936,32:1929}[w];reload_candidate=receipt['rows'][0]['reload'];assert reload_candidate['mismatches']==reload_candidate['fixups']==0 and reload_candidate['exit_code']==0
   assert all(sha(f)==h for f,h in reload_candidate['files'].items());candidate_route=next(Path(f) for f in reload_candidate['files'] if f.endswith('/design.route'));candidate_log=next(Path(f) for f in reload_candidate['files'] if f.endswith('/reload.log'))
   candidate=dict(cpd_ns=v['candidate_cpd_ns'],wirelength=wire(candidate_log));bindings[str(candidate_route)]=sha(candidate_route);bindings[str(candidate_log)]=sha(candidate_log)
   assert abs(Fraction(str(gv['rows'][0]['reference_cpd_ns']))-Fraction(reference['cpd_ns']))<=Fraction(51,1000000)
  decision=decide(candidate,reference);selected=candidate_route if decision['selected']=='candidate' else route;assert selected is not None
  work=OUT/f'w{w}_m{i}';work.mkdir();start=time.perf_counter();ctx=PersistentRCContext(case['targets'][0]);state=import_native_ledger(ctx,selected)
  snapshot=work/'accepted_state.json';snapshot.write_text(json.dumps(dict(revision=1,records=[state.records[k] for k in sorted(state.records)],ledger=dict(state.ledger),endpoint_metadata=ctx.endpoint_metadata,scale=ctx.rc.scale),indent=2)+'\n')
  rows.append(dict(width=w,index=i,prediction_status=pred['status'],decision=decision,candidate_metrics=candidate,reference_metrics=reference,selected_route=str(selected),selected_route_sha256=sha(selected),snapshot_sha256=sha(snapshot),connections=len(state.records),standalone_context_import_serialization_seconds=time.perf_counter()-start))
  print(w,i,decision,flush=True)
  (OUT/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(OUT/'protocol.json'),bindings=bindings,rows=rows,scope='Native-content admission/handoff replay for all12. Standalone context/import timer is not complete live accepted lifecycle or speedup.'),indent=2)+'\n')
if __name__=='__main__':
 import sys
 if sys.argv[1:] == ['--initialize']:initialize()
 else:run()
