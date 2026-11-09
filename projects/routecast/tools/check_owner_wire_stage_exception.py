"""Inject after endpoint/owner/history/demand mutations; retained state survives."""
import json,copy
from pathlib import Path
from owner_union_wire_rc_context import OwnerUnionWireRCContext
from native_route_ledger_import import import_native_ledger
import connection_budget_owner_wire_staged_reroute as staging
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];p=json.loads((ROOT/'experiments/mux_owner_union_wire_fixed_cap_cohort_2026-10-07/protocol.json').read_text());case=p['cases'][0];ctx=OwnerUnionWireRCContext(case['old']);route=Path(ctx.endpoint_metadata['inputs']['net']['path']).parent/'design.route';state=import_native_ledger(ctx,route);owner=next(v for v in state.unions.values() if v);node=next(n for n in ctx.destination_slots if ctx.wire_lengths[n]);ctx.restore_wire_state({node:3},owner);ctx.native.set_other({node:1});before_context=ctx.context;before_metadata=ctx.endpoint_metadata;before=(dict(ctx.history),ctx.wire_owner_union,list(ctx.native.arrays[3]),list(ctx.native.other),copy.deepcopy(state.records),copy.deepcopy(state.unions),copy.deepcopy(state.parents),dict(state.ledger));original_query=ctx.query;count=0
class InjectedFailure(RuntimeError):pass
def failing(*args,**kwargs):
 global count
 count+=1;ctx.set_history({node:17});ctx.native.set_other({node:2});raise InjectedFailure('query fault after owner binding and native mutation')
ctx.query=failing
try:
 staging.stage_reroute_with_repair(state,case['target'])
except InjectedFailure:pass
else:raise AssertionError('fault did not propagate')
finally:ctx.query=original_query
assert count==1 and ctx.context is before_context and ctx.endpoint_metadata is before_metadata
assert before==(dict(ctx.history),ctx.wire_owner_union,list(ctx.native.arrays[3]),list(ctx.native.other),state.records,state.unions,state.parents,dict(state.ledger))
out=ROOT/'experiments/owner_wire_stage_exception_contract_2026-10-07';out.mkdir(exist_ok=True);(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),context_sha256=sha(ROOT/'tools/owner_union_wire_rc_context.py'),stage_sha256=sha(ROOT/'tools/connection_budget_owner_wire_staged_reroute.py'),old_route_sha256=sha(route),target_sha256=sha(case['target']),scope='Injected private-stage query failure after endpoint/owner binding and explicit history/native demand changes. Exact owner/history/cost/demand/context/metadata and original retained records/unions/parents/ledger restoration; no accepted publication or concurrent-reader contract.'),indent=2)+'\n');print('Private owner-wire stage exception restoration verified',flush=True)
