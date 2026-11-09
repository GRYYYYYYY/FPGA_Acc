"""Real graph history replacement/reset and rejected-update isolation checks."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_persistent_context_contract_2026-10-06';out.mkdir();fixtures=root/'experiments/ex5p_context_reuse_2026-10-06/fixtures.json';prior=root/'experiments/ex5p_budget_repair_2026-10-06/receipt.json';ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json'
p={'endpoint_sha256':sha(ep),'fixtures_sha256':sha(fixtures),'prior_sha256':sha(prior),'context_source_sha256':sha(root/'tools/persistent_rc_context.py'),'scope':'Real graph exact history replacement and rejection isolation; synchronous single-owner interface, no whole-route rollback or concurrent atomicity claim.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(ep);f=json.loads(fixtures.read_text());history={int(n):c for n,c in json.loads(prior.read_text())['history'].items()};snapshots=[]
for h in [history,{},history,{},history]:
 ctx.set_history(h)
 assert all(c==ctx.rc.increments[s]*(1+h.get(ctx.rc.fields['dest_ranks'][s],0)) for s,c in enumerate(ctx.native.arrays[3]))
 snapshots.append(dict(ctx.history))
class Broken:
 def items(self):
  yield next(iter(history)),0
  raise RuntimeError('interrupted history traversal')
node=next(s for s in range(ctx.native.n) if any(ctx.rc.increments[i]>0 for i in ctx.destination_slots.get(s,())))
bad=[{-1:1},{ctx.native.n:1},{node:-1},{node:True},{node:1<<64},Broken()];rejected=0
for h in bad:
 before=(ctx.native.arrays[3].tobytes(),dict(ctx.history),ctx.native.other.tobytes())
 try:ctx.set_history(h)
 except (ValueError,RuntimeError):rejected+=1
 else:raise AssertionError('invalid update accepted')
 assert before==(ctx.native.arrays[3].tobytes(),dict(ctx.history),ctx.native.other.tobytes())
ctx.reset();answers=[]
for i in [1171,0,169,0]:
 x=f[str(i)];q=x['query'];a=ctx.query(q['source'],q['sink'],ctx.rc.scale//10**9,{int(n):c for n,c in x['other'].items()});assert a==x['expected'];answers.append({'index':i,'answer':a})
ctx.reset();assert not ctx.history and not any(ctx.native.other);assert list(ctx.native.arrays[3])==list(ctx.rc.increments)
r={'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'history_transitions':snapshots,'invalid_updates_rejected_without_mutation':rejected,'answers':answers,'reset_verified':True,'wall_s':time.monotonic()-start};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('verified',len(snapshots),'history transitions,',rejected,'rejected updates,',len(answers),'exact query answers; reset')
