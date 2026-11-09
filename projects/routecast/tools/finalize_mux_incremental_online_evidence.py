"""Final full-cohort incremental result/cost/native-content evidence bundle."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_net_slack_incremental_online_loop_2026-10-06'
base=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06'
def read(p):return json.loads(p.read_text())
r=read(out/'receipt.json');a=read(out/'audit_summary.json');e=read(out/'exact_result_equivalence.json');cost=read(out/'cost_lower_bound_snapshot.json')
assert len(r['rows'])==12 and a['receipt_sha256']==sha(out/'receipt.json')
assert e['pending']==0 and len(e['rows'])==12
assert cost['online_receipt_sha256']==sha(out/'receipt.json') and len(cost['rows'])==12
assert a['statuses']=={'COMPLETE_CANDIDATE':2,'ATTEMPT_LIMIT':6,'PRIOR_ALLOCATION_SKIP':4}
rows=[]
for row,c in zip(r['rows'],cost['rows']):
 w,i=row['width'],row['index'];assert (w,i)==(c['width'],c['index'])
 item=dict(width=w,index=i,status=row['status'],cost_lower_bound_s=c.get('recorded_cost_lower_bound_s'))
 if row['status']=='COMPLETE_CANDIDATE':
  proof=out/f'w{w}_m{i}/native_evidence_reuse.json';v=read(proof)
  assert v['result_sha256']==row['result_sha256']==sha(out/f'w{w}_m{i}/result.json')
  assert v['native_input_verification_sha256']==sha(out/f'w{w}_m{i}/native_input_verification.json')
  item.update(native_content_proof_sha256=sha(proof),selected=v['gate_selected'],candidate_cpd_ns=v['candidate_cpd_ns'],new_native_execution=False)
 else:item.update(selected=None,new_native_execution=False)
 rows.append(item)
(out/'final_evidence.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),files={str(out/f):sha(out/f) for f in ('receipt.json','audit_summary.json','exact_result_equivalence.json','cost_lower_bound_snapshot.json')},rows=rows,scope='Terminal all12 prospective outcomes and six independent case audits, exact old/new result parity, new preparation+actual reroute cost lower bounds. Two archived native CONTENT proofs reused, no new native execution/timers/publication. Component improvement only; no accepted lifecycle acceleration, improved completion/QoR or heldout generalization claim.'),indent=2)+'\n');print('final full12 incremental evidence bound')
