"""Fresh independent native capture comparison for relocated original identity."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from rebind_native_seed import rebind
from relocate_original_identity_v2 import OriginalIdentityRelocator
from source_binding import closure
R=Path(__file__).resolve().parents[2];s=R/'experiments/native_resume_cached_identity_adder_2026-10-07';o=s/'independent_rebind';o.mkdir(exist_ok=False);ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_2_endpoints.json';prev=R/'experiments/native_resume_cached_identity_adder_step2_workflow_2026-10-07/exchange_canonical/design.route';source=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits';inputs={str(p):sha(p) for p in (ep,prev,s/'rebind_step3/receipt.json',s/'rebind_step3/identity.jsonl',s/'rebind_step3/rebound.route')};sources=closure([Path(__file__)]);(o/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,scope='Retrospective independent fresh native original identity capture; costs excluded from workflow/cold clocks on both sides.'),indent=2)+'\n');ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inv=SharedRRInventory(ctx);seed,proof=rebind(ctx,inv,ep,prev,source,o/'fresh_native');assert (o/'fresh_native/identity.jsonl').read_bytes()==(s/'rebind_step3/identity.jsonl').read_bytes();assert seed.read_bytes()==(s/'rebind_step3/rebound.route').read_bytes()
base_ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';base=s/'rebind_step2';adapter=OriginalIdentityRelocator(base_ep,base/'identity.jsonl',base/'receipt.json',ctx.graph);bad=json.loads(ep.read_text());bad['net_names'][next(iter(bad['net_names']))]='wrong';badfile=o/'bad_endpoint.json';badfile.write_text(json.dumps(bad))
try:adapter.relocate(badfile,o/'bad_table.jsonl')
except ValueError:assert not (o/'bad_table.jsonl').exists()
else:raise AssertionError('wrong NET accepted')
# Enforce native-capture table hash/path rather than caller-supplied unbound table.
try:OriginalIdentityRelocator(base_ep,o/'fresh_native/identity.jsonl',base/'receipt.json',ctx.graph)
except ValueError:pass
else:raise AssertionError('foreign table accepted')
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(o/'verification.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,fresh_native_capture_exit_code=proof['identity_capture_exit_code'],identity_bytes_exact=True,rebound_route_bytes_exact=True,rejections=['wrong_NET_no_output','foreign_capture_table'],scope='Fresh native capture agrees with relocated table and exact seed route. Final native FULL/STA proofs recorded by full sequential verifier; no generic/concurrent cache-service claim.'),indent=2)+'\n');print('fresh native identity and seed exact; incompatible capture/NET rejected')
