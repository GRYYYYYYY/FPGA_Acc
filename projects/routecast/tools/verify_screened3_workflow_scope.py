"""Bind provisional decisions, skipped work, and final selected native proofs."""
import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from native_qor_admission import admit
ROOT=Path(__file__).resolve().parents[1];pair=ROOT/'experiments/bitonic_screened3_cost_pair_2026-10-07';out=ROOT/'experiments/bitonic_screened3_acceptance_workflow_2026-10-07';cold=ROOT/'experiments/bitonic_workflow_screened3_swapped_cold_2026-10-07';raw=ROOT/'experiments/bitonic_workflow_screened3_resident_staging_native_import_2026-10-07'
pr=json.loads((pair/'receipt.json').read_text());assert pr['complete'] and all(x['exit_code']==0 for x in pr['rows']);wr=json.loads((out/'receipt.json').read_text());assert wr['complete'];admissions=json.loads((cold/'admission.json').read_text());cr=json.loads((cold/'receipt.json').read_text());rr=json.loads((raw/'receipt.json').read_text());assert admissions['cold_receipt_sha256']==sha(cold/'receipt.json') and admissions['raw_receipt_sha256']==sha(raw/'receipt.json');assert admissions['rows']==[admit(c,r) for c,r in zip(cr['rows'],rr['rows'])];rows=[]
for a in admissions['rows']:
 n=a['count'];stage=next(x for x in wr['stages'] if x['stage']==f'trial_bitonic_resident_staging_n{n}_canonical.py');canonical=ROOT/f'experiments/bitonic_workflow_screened3_resident_staging_n{n}_canonical_2026-10-07'
 if not a['admitted']:
  assert stage['status']=='SKIPPED_QOR_REJECTED' and not (canonical/'receipt.json').exists()
 else:
  v=json.loads((canonical/'verification.json').read_text());assert v['receipt_sha256']==sha(canonical/'receipt.json');assert v['packing_fixups']==0 and v['before_after_named_physical_paths_unchanged'] and v['canonical_named_paths_exactly_match_native_postsync']
 rows.append(dict(count=n,provisional_admission=a['admitted'],reasons=a['reasons'],candidate_canonical_executed=a['admitted']))
e=json.loads((out/'final_evidence.json').read_text());assert all(sha(f)==d for f,d in e['artifacts_sha256'].items())
for a,b in zip(e['selected_workflow'],e['selected_baseline']):assert Fraction(a['cpd_ns'])<=Fraction(b['cpd_ns']) and a['wirelength']<=b['wirelength']
value=dict(source_sha256=sha(Path(__file__)),pair_receipt_sha256=sha(pair/'receipt.json'),workflow_receipt_sha256=sha(out/'receipt.json'),admission_sha256=sha(cold/'admission.json'),final_evidence_sha256=sha(out/'final_evidence.json'),rows=rows,workflow_seconds=e['workflow_seconds'],baseline_seconds=e['baseline_seconds'],ratio=e['workflow_over_baseline'],scope='Inherited generic canonical candidate descriptions apply ONLY to provisional admits: rejected4/8 canonical work omitted, both rejected candidates retained as raw native evidence. Final selected cold4/8 and candidate16 ALL zero-fixup FULL/STA/endpoints/ledger audited. Cold oracle remains charged to workflow. Additional scope audit outside both clocks; prepared inputs/single serial order/OS caches not reset, no stable raw-input gain claim.')
(pair/'verification.json').write_text(json.dumps(value,indent=2)+'\n');print(value)
