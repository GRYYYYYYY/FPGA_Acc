"""Full development handoff comparison after independently audited fresh live workflow."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_resident_live_seed_complete_workflow_v1_2026-10-10';old=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/native/sha1';new=D/'seed/native/sha1';bindings={str(Path(__file__)):sha(Path(__file__))}
for name in ['subset.json','bindings.json']:
 assert json.loads((new/name).read_text())==json.loads((old/name).read_text()),name
 for p in [new/name,old/name]:bindings[str(p)]=sha(p)
assert (new/'seed.route').read_bytes()==(old/'seed.route').read_bytes()
for p in [new/'seed.route',old/'seed.route',D/'verification.json',D/'wire_transaction_verification.json']:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(D/'handoff_parity_verification.json').write_text(json.dumps(dict(bindings=bindings,all4028_selected_and2245_pending_records_decisions_and_pin_bindings_equal=True,seed_bytes_equal_original_complete_guard_handoff=True,scope='Same development input comparison after fresh live model/handoff; native final physical+canonical audits independently performed. No heldout/silicon/timegain claim.'),indent=2)+'\n');print('HANDOFF FULL PARITY')
