"""All12 status snapshot, native acceptance distinct from selected publication."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06';p=json.loads((out/'protocol.json').read_text());rows=[]
for case in p['cases']:
 w,i=case['width'],case['index'];slack=ROOT/f'experiments/mux_net_slack_budgets_2026-10-06/w{w}_m{i}.json';seed=json.loads(slack.read_text());row=dict(width=w,index=i,budget_sha256=sha(slack))
 if seed['status']=='PRIOR_ALLOCATION_SKIP':row['status']='INITIAL_SKIP'
 else:
  file=out/f'w{w}_m{i}/result.json'
  if not file.exists():row['status']='ROUTE_PENDING'
  else:
   d=json.loads(file.read_text());row.update(result_sha256=sha(file),sketch_status=d['result']['status'])
   if d['result']['status']!='COMPLETE_CANDIDATE':row['status']='INCOMPLETE_NOT_SUBMITTED'
   elif (w,i)==(8,0):
    reuse=out/'w8_m0/native_evidence_reuse.json';v=json.loads(reuse.read_text());assert v['result_sha256']==sha(file);assert v['native_input_verification_sha256']==sha(out/'w8_m0/native_input_verification.json');assert v['gate_verification_sha256']==sha(ROOT/'experiments/mux_net_slack_focus_quality_gate_2026-10-06/verification.json') and v['candidate_canonical_verification_sha256']==sha(ROOT/'experiments/mux_net_slack_focus_candidate_canonical_2026-10-06/verification.json');row.update(status='NATIVE_VALIDATED_REFERENCE_SELECTED',candidate_cpd_ns=v['candidate_cpd_ns'],selected='reference',evidence_reuse_sha256=sha(reuse),native_execution_reused=True)
   elif (w,i)==(8,2):
    gate=ROOT/'experiments/mux_net_slack_w8m2_quality_gate_2026-10-06';canon=ROOT/'experiments/mux_net_slack_w8m2_candidate_canonical_2026-10-06';gv=json.loads((gate/'verification.json').read_text());cv=json.loads((canon/'verification.json').read_text());assert gv['receipt_sha256']==sha(gate/'receipt.json') and cv['receipt_sha256']==sha(canon/'receipt.json');snapshot=json.loads((gate/'parent_receipt_snapshot.json').read_text());assert snapshot['rows'][0]['result_sha256']==sha(file);gp=json.loads((gate/'protocol.json').read_text());assert gp['parent_receipt_sha256']==sha(gate/'parent_receipt_snapshot.json') and gp['native_input_verification_sha256']==sha(out/'w8_m2/native_input_verification.json');assert all(sha(f)==h for entry in json.loads((canon/'receipt.json').read_text())['rows'] for f,h in entry['reload']['files'].items());selected=gv['rows'][0]['selected'];row.update(status='NATIVE_VALIDATED_'+selected.upper()+'_SELECTED',candidate_cpd_ns=cv['candidate_cpd_ns'],selected=selected,gate_verification_sha256=sha(gate/'verification.json'),canonical_verification_sha256=sha(canon/'verification.json'),native_execution_reused=False)
   else:row['status']='NATIVE_PENDING'
   if 'candidate_cpd_ns' in row:assert F(row['candidate_cpd_ns'])<=F(seed['target_cpd_ns'])
 rows.append(row)
(out/'native_outcomes_snapshot.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),source_sha256=sha(Path(__file__)),rows=rows,native_validated=sum('candidate_cpd_ns' in r for r in rows),forecast_selected=sum(r.get('selected')=='predicted' for r in rows),scope='Available outcome snapshot includes all12 explicit pending/skips/incomplete. Candidate meets oldtarget distinct from better-reference selection. Reused evidence not new native execution/timer. No fullcohort/lifecyclegain claim.'),indent=2)+'\n');print('native validated',sum('candidate_cpd_ns' in r for r in rows),'forecast selected',sum(r.get('selected')=='predicted' for r in rows))
