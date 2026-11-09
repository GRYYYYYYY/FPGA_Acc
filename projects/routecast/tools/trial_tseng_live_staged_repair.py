"""Frozen same-policy real placement update on tseng; leave live state unchanged."""
import copy,json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from route_ledger_state import RouteLedgerState
from staged_placement_reroute import stage_reroute_with_repair
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_live_staged_repair_2026-10-06';out.mkdir()
ep=root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json';moved=root/'experiments/tseng_placement_swap_2026-10-06/endpoints.json';priorfile=root/'experiments/tseng_joint_transfer_2026-10-06/receipt.json'
prior=json.loads(priorfile.read_text());v=json.loads((priorfile.parent/'verification.json').read_text());assert v['receipt_sha256']==sha(priorfile) and v['accepted_paths_checked']==1234
p={'inputs_sha256':{str(x):sha(x) for x in (ep,moved,priorfile)},'sources_sha256':{n:sha(root/'tools'/n) for n in ('trial_tseng_live_staged_repair.py','persistent_rc_context.py','route_ledger_state.py','staged_placement_reroute.py','moved_history_repair_engine.py')},'policy':'Unchanged staged wholeNET reroute 1ns/10000labels, inherited history, at most4 frontier repair releases on UNREACHABLE; no metric-driven selection or extension; no live publication.'}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(ep);state=RouteLedgerState(ctx);ctx.set_history({int(n):c for n,c in prior.get('history',{}).items()})
for rec in prior['records']:
 net=rec['net_id'];state.records[rec['connection_id']]=rec;state.unions[net].add(rec['source'])
 for eid in rec['answer']['physical_edge_ids']:
  u,n=state.slots[eid];state.unions[net].add(n);state.parents[net][n]=(u,eid)
state.ledger.update(n for used in state.unions.values() for n in used);setup=time.monotonic()-start
snapshot=copy.deepcopy((state.records,state.unions,state.parents,state.ledger));context=ctx.context;metadata=ctx.endpoint_metadata;buffers=[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
start=time.monotonic();result=stage_reroute_with_repair(state,moved);elapsed=time.monotonic()-start
assert ctx.context is context and ctx.endpoint_metadata is metadata
assert (state.records,state.unions,state.parents,state.ledger)==snapshot
assert buffers==[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
for name,r in [('incremental',result['incremental']),('receipt',result['repair'] or result['incremental'])]:
 r=dict(r);r.update(protocol_sha256=sha(out/'protocol.json'),source_sha256=sha(Path(__file__)))
 (out/(name+'.json')).write_text(json.dumps(r,indent=2)+'\n')
summary={'context_setup_s':setup,'staged_update_s':elapsed,'repair_invoked':result['repair'] is not None,'status':result['status'],'live_state_restored':True,'receipt_sha256':sha(out/'receipt.json'),'protocol_sha256':sha(out/'protocol.json')}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
