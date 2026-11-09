"""After-run exact parity to prior text workflow, not a timing significance test."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
seq=R/'experiments/native_resume_live_binary_integrated_adder_2026-10-07';rows=[];norm=lambda p:{n:Counter(ps) for n,ps in physical_paths(p).items() if ps}
for i in (1,2,3):
 new=R/f'experiments/native_resume_live_binary_integrated_adder_step{i}_workflow_2026-10-07';old=R/f'experiments/native_resume_live_integrated_adder_step{i}_workflow_2026-10-07';a=json.loads((new/'receipt.json').read_text());b=json.loads((old/'receipt.json').read_text());assert a['cpd_ns']==b['cpd_ns'] and a['wirelength']==b['wirelength']
 for stage in ('canonical','exchange_canonical'):assert norm(new/stage/'design.route')==norm(old/stage/'design.route')
 for file in ('design.net','design.place','design.route','report_timing.setup.rpt'):assert (new/'exchange_canonical'/file).read_bytes()==(old/'exchange_canonical'/file).read_bytes()
 assert (new/'exchange_native/live.search/exchange/output.jsonl').read_bytes()==(old/'exchange_native/live.search/exchange/output.jsonl').read_bytes()
 ag=json.loads((new/'exchange_native/live.search/budget/receipt.json').read_text());bg=json.loads((old/'exchange_native/live.search/budget/receipt.json').read_text());assert ag['records']==bg['records']
 for ar,br in zip(ag['rows'],bg['rows']):
  for k in ('net','delays','old_wire','new_wire','previous_total_wire','trial_total_wire','accepted','old_union','new_union','other_occupancy','trial_records'):assert ar[k]==br[k]
 rows.append(dict(index=i,first_and_final_paths_equal=True,final_route_net_place_timing_bytes_equal=True,exchange_all_attempts_bytes_equal=True,repair_records_decisions_owners_equal=True,new_receipt_sha256=sha(new/'receipt.json'),reference_receipt_sha256=sha(old/'receipt.json')))
(seq/'text_reference_parity.json').write_text(json.dumps(dict(rows=rows,verifier_sha256=sha(__file__),scope='Prior text reference is read only after new sequence completes. All final native bytes, paths and search decisions/owner states equal. Separate single-run elapsed clocks do not establish speed significance.'),indent=2)+'\n');print('PASS',len(rows))
