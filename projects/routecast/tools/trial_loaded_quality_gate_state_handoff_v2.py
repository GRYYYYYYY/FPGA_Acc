"""Import verified gate winners and replay next real placement update."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from staged_placement_reroute import stage_reroute_with_repair

ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/loaded_quality_gate_original_reload_2026-10-06'
receipt=json.loads((parent/'receipt.json').read_text())
assert json.loads((parent/'verification.json').read_text())['receipt_sha256']==sha(parent/'receipt.json')
out=ROOT/'experiments/loaded_quality_gate_state_handoff_v2_2026-10-06';out.mkdir()
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),source_sha256=sha(Path(__file__)),scope='Verified first winner route -> Python ledger -> live reverse placement prediction. No second native quality gate or total cost evidence.'),indent=2)+'\n')
rows=[]
for width in (32,64,128):
    route=parent/f'gf2_d{width}_A/design.route'
    target=ROOT/f'experiments/gf2_d{width}_placement_swap_2026-10-06/endpoints.json'
    ctx=PersistentRCContext(target);state=import_native_ledger(ctx,route)
    old=ROOT/f'experiments/gf2_continuous_two_updates_v2_2026-10-06/gf2_d{width}_accepted1.json'
    expected=json.loads(old.read_text())
    records=[state.records[k] for k in sorted(state.records)]
    assert records==expected['records'] and {str(k):v for k,v in state.ledger.items()}==expected['ledger']
    original=ROOT/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{width}/endpoints.json'
    answer=stage_reroute_with_repair(state,original);candidate=answer['repair'] or answer['incremental']
    assert candidate['failure'] is None
    archived=ROOT/f'work/gf2_certified_continuous_two_updates_2026-10-06/gf2_d{width}/1/experiments/gf2_selected_reverse_updates_2026-10-06/gf2_d{width}/receipt.json'
    prior=json.loads(archived.read_text())
    assert candidate['records']==prior['records'] and {str(k):v for k,v in candidate['ledger'].items()}==prior['ledger']
    result=out/f'gf2_d{width}_reverse_prediction.json';result.write_text(json.dumps(candidate,indent=2)+'\n')
    rows.append(dict(width=width,route_sha256=sha(route),first_snapshot_sha256=sha(old),archived_reverse_sha256=sha(archived),reverse_result_sha256=sha(result),connections=len(records),first_state_exact=True,next_prediction_records_ledger_exact=True))
    print(width,'handoff and reverse prediction parity',len(records),flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
