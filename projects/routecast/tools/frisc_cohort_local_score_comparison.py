"""Compare every reported candidate with the full-score reference run."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ref=Path('experiments/frisc_incremental_budget_cohort_2026-10-05')
new=Path('experiments/frisc_incremental_budget_cohort_local_score_2026-10-05')
a=json.loads((ref/'receipt.json').read_text());b=json.loads((new/'receipt.json').read_text())
assert a['input_sha256']==b['input_sha256']
assert len(a['reports'])==len(b['reports'])==617
for x,y in zip(a['reports'],b['reports']):
 assert {k:v for k,v in x.items() if k!='query_s'}=={k:v for k,v in y.items() if k!='query_s'}
assert (ref/'prediction.json').read_bytes()==(new/'prediction.json').read_bytes()
assert a['baseline_scores']==b['baseline_scores'] and a['final_scores']==b['final_scores']
r={'reference_receipt_sha256':sha(ref/'receipt.json'),'local_receipt_sha256':sha(new/'receipt.json'),'comparison_source_sha256':sha(__file__),'queries':617,'all_reported_candidate_scores_and_outcomes_equal':True,'final_prediction_bytes_equal':True,'reference_wall_s':a['full_wall_s'],'local_wall_s':b['full_wall_s'],'reference_score_s':a['stage_seconds']['full_score_and_occupancy_export'],'local_score_s':b['stage_seconds']['local_score'],'scope':'Same development five-net workload with external context refreshed at each net boundary; timing is descriptive on shared host. Noncommitted paths were not archived. No end-to-end, hardware, or unseen-design claim.'}
(new/'comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
