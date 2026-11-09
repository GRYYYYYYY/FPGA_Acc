"""Exact prepared-input parity; separately timed fresh buffered repair."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from source_binding import closure
from current_global_budget_buffered import repair
R=Path(__file__).resolve().parents[2];out=R/'experiments/native_resume_global_budget_buffer_parity_2026-10-07';out.mkdir(exist_ok=False);inputs={}
for i in (1,2,3):
 b=R/f'experiments/native_resume_global_budget_adder_step{i}_workflow_2026-10-07'
 for p in (b/'global_budget/receipt.json',b/'exchange/receipt.json',b/'canonical/report_timing.setup.rpt',R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json'):inputs[str(p)]=sha(p)
protocol=dict(inputs=inputs,sources=closure([Path(__file__)]),scope='Same archived own-state inputs; compare all conditioned binary payload/output bytes, trees and decisions. Timed buffered calls fresh, old times historical not controlled comparison. No native or full net-gain claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
start=time.perf_counter();ctx=ReusableRRFloors(R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json',R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);bootstrap=time.perf_counter()-start
for i in (1,2,3):
 b=R/f'experiments/native_resume_global_budget_adder_step{i}_workflow_2026-10-07';old=json.loads((b/'global_budget/receipt.json').read_text());records=json.loads((b/'exchange/receipt.json').read_text())['records'];r=repair(ctx,inv,R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json',records,b/'canonical/report_timing.setup.rpt',old['budget'],out/f'step{i}')
 assert r['records']==old['records'] and r['rows']==old['rows'];assert all(r[k]==old[k] for k in ('initial_wire','final_wire','budget','scale'))
 for n in range(len(r['rows'])):
  for suffix in ('bin','jsonl'):assert (out/f'step{i}/net_{n}.{suffix}').read_bytes()==(b/f'global_budget/net_{n}.{suffix}').read_bytes()
 rows.append(dict(index=i,connections=sum(len(x['delays']) for x in r['rows']),buffered_seconds=r['total_seconds'],historical_seconds=old['total_seconds'],exact_payload_output_rows_and_full_paths=True));print(rows[-1],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**protocol['sources']}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),bootstrap_seconds=bootstrap,rows=rows,scope=protocol['scope']),indent=2)+'\n')
