"""After-run full native/search/owner parity against unbatched local policy."""
import sys,json
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
seq=R/'experiments/native_resume_postroute_identity_only_adder_2026-10-07';rows=[];norm=lambda p:{n:Counter(ps) for n,ps in physical_paths(p).items() if ps}
for i in (1,2,3):
 a=R/f'experiments/native_resume_postroute_identity_only_adder_step{i}_workflow_2026-10-07';b=R/f'experiments/native_resume_postroute_local_integrated_adder_step{i}_workflow_2026-10-07'
 for file in ('first/live.parent.route','first/candidate.route','canonical/design.route'):assert norm(a/file)==norm(b/file)
 for file in ('design.net','design.place','design.route','report_timing.setup.rpt'):assert (a/'canonical'/file).read_bytes()==(b/'canonical'/file).read_bytes()
 assert (a/'first/live.search/exchange/output.jsonl').read_bytes()==(b/'first/live.search/exchange/output.jsonl').read_bytes()
 new=json.loads((a/'first/live.search/budget/receipt.json').read_text());old=json.loads((b/'first/live.search/budget/receipt.json').read_text());assert new['records']==old['records'] and new['final_wire']==old['final_wire'];assert len(new['rows'])==len(old['rows'])
 for ar,br in zip(new['rows'],old['rows']):
  for key in ('net','delays','accepted','old_wire','new_wire','previous_total_wire','trial_total_wire','old_union','new_union','other_occupancy','trial_records'):assert ar[key]==br[key]
 rows.append(dict(index=i,initial_candidate_final_paths_equal=True,final_route_net_place_timing_bytes_equal=True,exchange_bytes_equal=True,budget_decisions_paths_delays_owners_equal=True,new_receipt_sha256=sha(a/'receipt.json'),reference_receipt_sha256=sha(b/'receipt.json')))
(seq/'batch_reference_parity.json').write_text(json.dumps(dict(rows=rows,verifier_sha256=sha(__file__),scope='Old reference read only after new sequence. Native path/byte parity and all sequential budget/owner decisions; independent runs not controlled performance significance.'),indent=2)+'\n');print('PASS',len(rows))
