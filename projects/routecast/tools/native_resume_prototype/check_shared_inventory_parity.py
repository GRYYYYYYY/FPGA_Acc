import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from audit_shared_inventory import audit as shared_audit
from serialize_shared_inventory import serialize as shared_serialize
from stream_native_route_audit_cached import audit
from serialize_live_native_candidate import serialize
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);out=ROOT/f'experiments/native_resume_shared_inventory_parity_w{w}_2026-10-07';out.mkdir(exist_ok=False);begin=time.perf_counter();ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';base=ROOT/f'experiments/native_resume_shared_pipeline_w{w}_m{i}_workflow_2026-10-07';ctx=ReusableRRFloors(ep,ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'floor_context');inventory=SharedRRInventory(ctx);built=time.perf_counter();route=base/'exchange_canonical/design.route';assert shared_audit(ctx.graph,route,inventory)==audit(ctx.graph,route);candidate=json.loads((base/'exchange/receipt.json').read_text());args=(candidate,ep,base/'canonical/identity.jsonl',base/'exchange_native/design.place');assert shared_serialize(*args,inventory)==serialize(*args);files=(ep,ctx.graph,route,base/'exchange/receipt.json',args[2],args[3],Path(__file__));result=dict(bindings={str(f):sha(f) for f in files},serialization_bytes_and_bindings_exact=True,complete_audit_dictionary_exact=True,inventory_and_context_seconds=built-begin,total_parity_seconds=time.perf_counter()-begin);(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(w,result)
