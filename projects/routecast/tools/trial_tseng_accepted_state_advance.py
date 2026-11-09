"""Real selected-reference state advancement and rejection/rollback contracts."""
import copy,json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from accepted_route_state import AcceptedRouteState,state_digest
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_accepted_state_advance_2026-10-06';out.mkdir()
e=root/'experiments';swapped=e/'tseng_placement_swap_2026-10-06/endpoints.json';original=e/'nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json'
gates=[e/'tseng_reverse_quality_gate_2026-10-06',e/'tseng_swapped_quality_gate_2026-10-06']
protocol={'sources_sha256':{n:sha(root/'tools'/n) for n in ('accepted_route_state.py','native_route_ledger_import.py','persistent_rc_context.py','trial_tseng_accepted_state_advance.py')},'inputs_sha256':{str(p):sha(p) for p in (swapped,original,*[p/name for p in gates for name in ('selection.json','verification.json','protocol.json')])},'scope':'Synchronous single-owner actual quality-selected reference advancement; archived native acceptance used, no new QoR measurement or disk/concurrent publication.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');ctx=PersistentRCContext(swapped);state=import_native_ledger(ctx,root/'work/tseng_swapped_quality_gate_2026-10-06/design.route');owner=AcceptedRouteState(state);checks=[];rows=[]
def snap():return (owner.token(),ctx.context,ctx.endpoint_metadata,owner.state,[a.tobytes() for a in ctx.native.arrays],ctx.native.other.tobytes())
def unchanged(s):
 assert owner.token()==s[0] and ctx.context is s[1] and ctx.endpoint_metadata is s[2] and owner.state is s[3] and [a.tobytes() for a in ctx.native.arrays]==s[4] and ctx.native.other.tobytes()==s[5]
def reject(label,fn):
 s=snap()
 try:fn()
 except ValueError:pass
 else:raise AssertionError(label+' did not reject')
 unchanged(s);checks.append(label)
reject('wrong-placement-selection',lambda:owner.prepare(swapped,gates[0]/'selection.json',gates[0]/'verification.json',owner.token()))
for i,(ep,gate) in enumerate(zip((original,swapped),gates)):
 s=snap();t=time.monotonic();prepared=owner.prepare(ep,gate/'selection.json',gate/'verification.json',owner.token());prepare_s=time.monotonic()-t;unchanged(s)
 if i==0:
  first=next(iter(prepared['state'].records));old=prepared['state'].records[first]['answer']['delay'];prepared['state'].records[first]['answer']['delay']=old+1
  reject('mutated-prepared-ledger',lambda:owner.advance(prepared));prepared['state'].records[first]['answer']['delay']=old
  ctx.set_history({0:1});ctx.native.set_other({0:1})
  # History change invalidates earlier preparation, prepare again at current token.
  reject('stale-history-token',lambda:owner.advance(prepared))
  prepared=owner.prepare(ep,gate/'selection.json',gate/'verification.json',owner.token())
  original_set=ctx.native.set_other;calls=[0];saved=snap()
  def injected(other):
   calls[0]+=1
   if calls[0]==1:raise RuntimeError('injected demand-buffer reset failure')
   return original_set(other)
  ctx.native.set_other=injected
  try:
   try:owner.advance(prepared)
   except RuntimeError:pass
   else:raise AssertionError('missing reset failure')
  finally:ctx.native.set_other=original_set
  unchanged(saved);checks.append('reset-exception-restores-history-demand-state')
 t=time.monotonic();owner.advance(prepared);advance_s=time.monotonic()-t
 reject('consumed-preparation-'+str(i),lambda:owner.advance(prepared))
 assert ctx.history=={} and not ctx.native.previous and len(owner.state.records)==1234
 snapshot={'records':[owner.state.records[c] for c in sorted(owner.state.records)],'ledger':dict(owner.state.ledger),'scale':ctx.rc.scale,'graph_sha256':ctx.context[1]};path=out/f'state{i}.json';path.write_text(json.dumps(snapshot,indent=2)+'\n')
 rows.append({'revision':owner.revision,'endpoint_path':str(ep),'gate':str(gate),'state_sha256':sha(path),'prepare_s':prepare_s,'advance_s':advance_s,'ledger_digest':state_digest(owner.state)})
r={'protocol_sha256':sha(out/'protocol.json'),'states':rows,'checks':checks,'final_revision':owner.revision,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
