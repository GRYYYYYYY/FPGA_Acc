"""Bind terminal cohort, qualified native content and controlled comparison."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07';baseline=ROOT/'experiments/mux_lazy_budget_cache_cohort_2026-10-06'
def read(p):return json.loads(p.read_text())
r=read(out/'receipt.json');p=read(out/'protocol.json');a=read(out/'audit_summary.json');cost=read(out/'cost_lower_bound_snapshot.json');cache=read(out/'cache_verification.json')
assert len(r['rows'])==12 and all(x['receipt_sha256']==sha(out/'receipt.json') for x in (a,cache))
assert cost['online_receipt_sha256']==sha(out/'receipt.json') and len(cost['rows'])==12
assert p['cases']==read(baseline/'protocol.json')['cases'] and p['certified_baseline_evidence_sha256']==sha(baseline/'final_evidence.json')
rows=[]
for row,c in zip(r['rows'],cost['rows']):
 w,i=row['width'],row['index'];assert (w,i)==(c['width'],c['index'])
 item=dict(width=w,index=i,status=row['status'],cost_lower_bound_s=c.get('recorded_cost_lower_bound_s'))
 if row['status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING':
  work=out/f'w{w}_m{i}';proof=read(work/'native_input_verification.json');assert proof['result_sha256']==sha(work/'result.json')==row['result_sha256']
  if i in (0,2):
   reuse=read(work/'native_evidence_reuse.json');assert reuse['result_sha256']==row['result_sha256'] and reuse['predicted_route_sha256']==sha(work/'predicted.route')
   item.update(selected=reuse['gate_selected'],native_cpd_ns=reuse['candidate_cpd_ns'],native_evidence_sha256=sha(work/'native_evidence_reuse.json'),new_native_execution=False)
  else:
   assert (w,i)==(8,3)
   gate=ROOT/'experiments/mux_heuristic_w8m3_quality_gate_2026-10-07';canonical=ROOT/'experiments/mux_heuristic_w8m3_candidate_canonical_2026-10-07';gv=read(gate/'verification.json');cv=read(canonical/'verification.json')
   assert gv['receipt_sha256']==sha(gate/'receipt.json') and cv['receipt_sha256']==sha(canonical/'receipt.json')
   assert cv['candidate_route_sha256']==sha(gate/'w8_m3/predicted.route')
   assert all(sha(f)==h for rr in read(canonical/'receipt.json')['rows'] for f,h in rr['reload']['files'].items())
   assert read(gate/'protocol.json')['native_input_verification_sha256']==sha(work/'native_input_verification.json')
   item.update(selected=gv['rows'][0]['selected'],native_cpd_ns=cv['candidate_cpd_ns'],native_evidence_sha256=sha(gate/'verification.json'),candidate_canonical_sha256=sha(canonical/'verification.json'),new_native_execution=True)
  item['native_status']='NATIVE_CONTENT_VALIDATED'
 else:item.update(selected=None,native_status='NOT_SUBMITTED',new_native_execution=False)
 rows.append(item)
assert sum(x['native_status']=='NATIVE_CONTENT_VALIDATED' for x in rows)==3 and sum(x['selected']=='predicted' for x in rows)==2
(out/'final_evidence.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),files={str(out/f):sha(out/f) for f in ('receipt.json','audit_summary.json','cost_lower_bound_snapshot.json','cache_verification.json')},rows=rows,baseline_complete=2,current_complete=3,forecast_selected=2,scope='Fixed12 controlled heuristic envelope relaxation, actual-delay DAG postcheck and independent six case audits. Three native-content qualified candidates: one fresh gate/owncanonical execution and two archived-content reserialization proofs; no accepted sequential publication. Completion improved vs certified baseline, earlier reported-joint already achieves same bestCPD/two forecast selections. Recorded setup+sketch lowerbounds exceed cold accepted observation in every searchedcase; all originalfloor/native/audit/import costs still additional. No generalization/board/end-to-end netgain claim.'),indent=2)+'\n');print('final full12 heuristic evidence bound;3nativevalid,2forecastselected')
