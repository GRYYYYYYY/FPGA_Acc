"""Rehydrate selected reference, not rejected prediction, for next update."""
import copy,json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger,physical_paths
from staged_placement_reroute import stage_reroute_with_repair
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_selected_reference_import_2026-10-06';out.mkdir()
gate=root/'experiments/tseng_swapped_quality_gate_2026-10-06';selection=json.loads((gate/'selection.json').read_text());verification=json.loads((gate/'verification.json').read_text());assert selection['selected']=='reference' and verification['FULL_reload_success'] and verification['selection_sha256']==sha(gate/'selection.json')
selected=root/'work/tseng_swapped_quality_gate_2026-10-06/design.route';ep=root/'experiments/tseng_placement_swap_2026-10-06/endpoints.json';target=root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json'
assert str(selected) in selection['files_sha256'] and sha(selected)==selection['files_sha256'][str(selected)]
p={'inputs_sha256':{str(p):sha(p) for p in (selected,ep,target,gate/'selection.json',gate/'verification.json')},'sources_sha256':{n:sha(root/'tools'/n) for n in ('native_route_ledger_import.py','persistent_rc_context.py','staged_placement_reroute.py','moved_history_repair_engine.py','trial_tseng_selected_reference_import.py')},'policy':'Import actual quality-selected native reference; no native timing budget imposed on retained branches. Next update reverses fixed swap, unchanged1ns/10000/max4 staged policy; no publication.'}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');t=time.monotonic();ctx=PersistentRCContext(ep);setup=time.monotonic()-t;t=time.monotonic();state=import_native_ledger(ctx,selected);import_s=time.monotonic()-t
snapshot=copy.deepcopy((state.records,state.unions,state.parents,state.ledger));context=ctx.context;metadata=ctx.endpoint_metadata;buffers=[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
t=time.monotonic();update=stage_reroute_with_repair(state,target);update_s=time.monotonic()-t
assert context is ctx.context and metadata is ctx.endpoint_metadata and snapshot==(state.records,state.unions,state.parents,state.ledger)
assert buffers==[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
incumbent={'records':[state.records[c] for c in sorted(state.records)],'ledger':dict(state.ledger),'scale':ctx.rc.scale,'graph_sha256':ctx.context[1]};(out/'incumbent.json').write_text(json.dumps(incumbent,indent=2)+'\n')
(out/'update.json').write_text(json.dumps(update,indent=2)+'\n');r={'connections':len(state.records),'context_setup_s':setup,'reference_import_s':import_s,'next_update_s':update_s,'next_status':update['status'],'repair_invoked':update['repair'] is not None,'live_state_restored':True,'retained_branches_over_1ns':sum(rec['answer']['delay']>ctx.rc.scale//10**9 for rec in state.records.values()),'protocol_sha256':sha(out/'protocol.json'),'incumbent_sha256':sha(out/'incumbent.json'),'update_sha256':sha(out/'update.json')};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
