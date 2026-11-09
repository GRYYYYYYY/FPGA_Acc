"""Intermediate conversion without duplicate original-native analysis, exact bytes."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from source_binding import closure
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from prepare_canonical_inventory import prepare_canonical
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_resume_canonical_preparation_parity_2026-10-07';o.mkdir(exist_ok=False);bindings={}
for i in (1,2,3):
 b=R/f'experiments/native_resume_all_inventory_adder_step{i}_workflow_2026-10-07';r=json.loads((b/'receipt.json').read_text());bindings[str(b/'receipt.json')]=sha(b/'receipt.json');bindings.update({str(f):sha(f) for folder in ('first','canonical') for f in (b/folder).iterdir() if f.is_file()})
p=dict(inputs=bindings,sources=closure([Path(__file__)]),scope='Own initial private-native output preparation parity vs archived original-native canonical FULL/STA reference. No new native final acceptance or timing gain.')
(o/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');ctx=ReusableRRFloors(R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json',R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inv=SharedRRInventory(ctx);rows=[]
for i in (1,2,3):
 b=R/f'experiments/native_resume_all_inventory_adder_step{i}_workflow_2026-10-07';r=json.loads((b/'receipt.json').read_text());native=next(x['native'] for x in r['stages'] if x['stage']=='first');meta=dict(native,cpd_ns=float(native['cpd_ns']));start=time.perf_counter();result=prepare_canonical(meta,b/'first',o/f'step{i}',inv)
 for f in ('design.blif','design.net','design.place','design.route','identity.jsonl','report_timing.setup.rpt'):assert (o/f'step{i}'/f).read_bytes()==(b/'canonical'/f).read_bytes(),f
 assert not result['native_analysis_performed'] and not (o/f'step{i}/reload.log').exists();rows.append(dict(index=i,seconds=time.perf_counter()-start,exact_route_net_place_identity_setup_report=True));print(rows[-1],flush=True)
assert all(sha(f)==h for f,h in {**bindings,**p['sources']}.items());(o/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(o/'protocol.json'),rows=rows,scope=p['scope']),indent=2)+'\n')
