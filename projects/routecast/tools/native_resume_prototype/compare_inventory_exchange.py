"""Exact all-NET exchange payload and decision parity using inventory CHAN spans."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from source_binding import closure
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from shared_inventory_exchange import exchange
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_resume_inventory_exchange_parity_2026-10-07';o.mkdir(exist_ok=False);inputs={}
for i in (1,2,3):
 b=R/f'experiments/native_resume_reload_inventory_adder_step{i}_workflow_2026-10-07'
 for p in (b/'exchange/receipt.json',b/'exchange/input.txt',b/'exchange/output.jsonl',b/'canonical/design.route',b/'canonical/report_timing.setup.rpt'):inputs[str(p)]=sha(p)
protocol=dict(inputs=inputs,sources=closure([Path(__file__)]),scope='Fresh shared-inventory exchange on archived own-state inputs; all input/output bytes and paths parity. Historical time not controlled acceleration evidence.')
(o/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();ctx=ReusableRRFloors(R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json',R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inv=SharedRRInventory(ctx);bootstrap=time.perf_counter()-start;rows=[]
for i in (1,2,3):
 b=R/f'experiments/native_resume_reload_inventory_adder_step{i}_workflow_2026-10-07';old=json.loads((b/'exchange/receipt.json').read_text());r=exchange(ctx,R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json',b/'canonical/design.route',o/f'step{i}',inv)
 for f in ('input.txt','output.jsonl'):assert (o/f'step{i}'/f).read_bytes()==(b/'exchange'/f).read_bytes()
 for k in ('records','selected_net_names','all_target_endpoints_and_capacity_verified','unchanged_floor_cache'):assert r[k]==old[k]
 rows.append(dict(index=i,connections=len(r['records']),total_seconds=r['total_seconds'],historical_seconds=old['total_seconds'],exact_payload_output_fullpaths_schedule=True));print(rows[-1],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**protocol['sources']}.items());(o/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(o/'protocol.json'),bootstrap_seconds=bootstrap,rows=rows,scope=protocol['scope']),indent=2)+'\n')
