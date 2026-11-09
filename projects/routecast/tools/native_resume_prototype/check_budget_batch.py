"""Exact sequential budget parity to previous per-NET process policy."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(Path(__file__).resolve().parent)]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from indexed_integer_rc import IndexedIntegerRC
from current_global_budget_batch import repair
out=R/'experiments/native_budget_batch_parity_2026-10-07';out.mkdir();ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);ctx.rc=IndexedIntegerRC(ctx.rc,ctx.fields,ctx.initial,inv);rows=[]
for i in (1,2,3):
 ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';base=R/f'experiments/native_resume_postroute_local_integrated_adder_step{i}_workflow_2026-10-07/first/live.search';old=json.loads((base/'budget/receipt.json').read_text());ex=json.loads((base/'exchange/receipt.json').read_text());producer=json.loads((base/'receipt.json').read_text());report=Path(next(p for p in old['bindings'] if p.endswith('.rpt')));r=repair(ctx,inv,ep,ex['records'],report,producer['initial_wire_budget'],out/f'step_{i}')
 for key in ('records','initial_wire','final_wire','budget','scale'):assert r[key]==old[key]
 assert len(r['rows'])==len(old['rows'])
 for a,b in zip(r['rows'],old['rows']):
  for key in ('net','delays','old_wire','new_wire','previous_total_wire','trial_total_wire','accepted','old_union','new_union','other_occupancy','trial_records'):assert a[key]==b[key],(i,key)
 rows.append(dict(index=i,all_decisions_paths_delays_owners_exact=True,queries=sum(len(row['delays']) for row in r['rows']),per_net_seconds=old['total_seconds'],batch_seconds=r['total_seconds'],batch_conversion_seconds=r['conversion_seconds'],batch_child_seconds=r['compiled_child_seconds'],reference_receipt_sha256=sha(base/'budget/receipt.json')))
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,checker_sha256=sha(__file__),scope='3 authentic sequential owner-state repairs, all decisions/path/integer-delay/owner union/wire parity to frozen per-NET process policy. Startup/context construction excluded from local parity time, complete paired native sequence evaluated separately.'),indent=2)+'\n');print(rows)
