"""Real swap staged using a live graph/ledger; verify normal/exception restoration."""
import copy,json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from route_ledger_state import RouteLedgerState
from staged_placement_reroute import stage_reroute
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_live_staged_reroute_2026-10-06';out.mkdir();ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';moved=root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json';priorfile=root/'experiments/ex5p_shared_ledger_engine_2026-10-06/3/receipt.json';prior=json.loads(priorfile.read_text());v=json.loads((priorfile.parent/'verification.json').read_text());assert v['receipt_sha256']==sha(priorfile);baselinefile=root/'experiments/ex5p_swap_incremental_2026-10-06/receipt.json';baseline=json.loads(baselinefile.read_text());p={'inputs_sha256':{str(x):sha(x) for x in (ep,moved,priorfile,baselinefile)},'sources_sha256':{n:sha(root/'tools'/n) for n in ('persistent_rc_context.py','route_ledger_state.py','staged_placement_reroute.py')},'policy':'One livecontext/ledger initialized from authenticated incumbent; genuine placement rebind, affectedwholeNET staging; no repairextension. Compare original frozenincremental outcomes and test injectedquery exception restoration.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(ep);state=RouteLedgerState(ctx);ctx.set_history({int(n):c for n,c in prior['history'].items()})
for r in prior['records']:
 net=r['net_id'];state.records[r['connection_id']]=r;state.unions[net].add(r['source'])
 for eid in r['answer']['physical_edge_ids']:u,n=state.slots[eid];state.unions[net].add(n);state.parents[net][n]=(u,eid)
state.ledger.update(n for used in state.unions.values() for n in used);setup=time.monotonic()-start;ctx.native.set_other({0:1});snapshot=copy.deepcopy((state.records,state.unions,state.parents,state.ledger));context=ctx.context;metadata=ctx.endpoint_metadata;buffers=[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
def restored():
 assert ctx.context is context and ctx.endpoint_metadata is metadata
 assert (state.records,state.unions,state.parents,state.ledger)==snapshot
 assert buffers==[a.tobytes() for a in ctx.native.arrays]+[ctx.native.other.tobytes()]
start=time.monotonic();r=stage_reroute(state,moved);elapsed=time.monotonic()-start;restored();normalized=json.loads(json.dumps(r))
for k in ('status','failure','events','records','ledger','completed_connections','required_connections'):assert normalized[k]==baseline[k],k
original_query=ctx.query;count=0
class InjectedFailure(RuntimeError):pass
def query(*args,**kwargs):
 global count
 count+=1
 if count==3:raise InjectedFailure('third query interruption')
 return original_query(*args,**kwargs)
ctx.query=query
try:
 try:stage_reroute(state,moved)
 except InjectedFailure:pass
 else:raise AssertionError('expected interruption')
finally:ctx.query=original_query
restored();r.pop('endpoint_metadata');r.update({'context_and_incumbent_setup_s':setup,'live_staged_reroute_s':elapsed,'normal_and_exception_restoration_verified':True,'algorithmic_parity':True,'parent_sha256':sha(priorfile),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))});(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'],r['completed_connections'],'setup',setup,'live stage',elapsed,'normal/exception restoration verified')
