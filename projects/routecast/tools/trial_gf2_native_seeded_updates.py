"""Posthoc initial-state ablation; same frozen swaps and search policy, native seed."""
import copy,json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from staged_placement_reroute import stage_reroute_with_repair
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_native_seeded_updates_2026-10-06';out.mkdir();cases=[]
for w in (32,64,128):
 original=root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}';ref=root/f'experiments/gf2_d{w}_fixed_original_cold_2026-10-06';q=json.loads((ref/'receipt.json').read_text());v=json.loads((ref/'verification.json').read_text());assert v['receipt_sha256']==sha(ref/'receipt.json');assert q['exit_code']==0
 route=root/f'work/gf2_d{w}_fixed_original_cold_2026-10-06/design.route';swap=root/f'experiments/gf2_d{w}_placement_swap_2026-10-06'
 cases.append({'width':w,'endpoints':str(original/'endpoints.json'),'route':str(route),'swap':str(swap/'endpoints.json'),'inputs_sha256':{str(p):sha(p) for p in (original/'endpoints.json',route,swap/'endpoints.json',ref/'receipt.json',ref/'verification.json')}})
p={'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ('persistent_rc_context.py','native_route_ledger_import.py','staged_placement_reroute.py','moved_history_repair_engine.py')},'scope':'Posthoc same frozen swap/policy native-seed ablation, initial routes authenticated FULL/STA native cold references; imported ledger not accepted published owner. Native retained branches need not obey new-search 1ns bound. No prospective no-native-input predictor claim.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
for case in cases:
 w=case['width'];d=out/f'gf2_d{w}';d.mkdir();t=time.monotonic();ctx=PersistentRCContext(case['endpoints']);state=import_native_ledger(ctx,case['route']);setup=time.monotonic()-t
 prior={'records':[state.records[c] for c in sorted(state.records)],'ledger':dict(state.ledger),'graph_sha256':ctx.endpoint_metadata['graph_sha256']};(d/'prior.json').write_text(json.dumps(prior,indent=2)+'\n')
 snapshot=copy.deepcopy((state.records,state.unions,state.parents,state.ledger));context=ctx.context;metadata=ctx.endpoint_metadata;arrays=[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()];t=time.monotonic();result=stage_reroute_with_repair(state,case['swap']);wall=time.monotonic()-t
 assert ctx.context is context and ctx.endpoint_metadata is metadata and snapshot==(state.records,state.unions,state.parents,state.ledger) and arrays==[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
 (d/'update.json').write_text(json.dumps(result,indent=2)+'\n');final=result['repair'] or result['incremental'];(d/'receipt.json').write_text(json.dumps(final,indent=2)+'\n');row={'width':w,'status':result['status'],'repair_invoked':result['repair'] is not None,'completed_connections':final['completed_connections'],'required_connections':final['required_connections'],'context_native_import_s':setup,'stage_and_repair_s':wall,'prior_sha256':sha(d/'prior.json'),'candidate_sha256':sha(d/'receipt.json'),'update_sha256':sha(d/'update.json'),'live_state_restored':True};rows.append(row);print(row,flush=True)
 assert all(sha(f)==h for f,h in case['inputs_sha256'].items())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':True},indent=2)+'\n')
