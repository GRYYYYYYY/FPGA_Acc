"""Real graph transition algebra, wire delta and exception preservation."""
import json,random
from pathlib import Path
from fractions import Fraction as F
from owner_union_wire_rc_context import OwnerUnionWireRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];p=json.loads((ROOT/'experiments/mux_wire_penalty_fixed_cap_cohort_2026-10-07/protocol.json').read_text());endpoint=p['cases'][0]['old'];ctx=OwnerUnionWireRCContext(endpoint);baseline=list(ctx.native.arrays[3]);rng=random.Random(20261007);nodes=list(ctx.destination_slots);checks=0
for _ in range(40):
 owner=set(rng.sample(nodes,min(20,len(nodes))));history={n:rng.randrange(5) for n in rng.sample(nodes,min(15,len(nodes)))};ctx.set_wire_owner_union(owner);ctx.set_history(history)
 expected=[v*(1+history.get(n,0))+(0 if n in owner else pen) for v,n,pen in zip(ctx.rc.increments,ctx.rc.fields['dest_ranks'],ctx.penalties)];assert list(ctx.native.arrays[3])==expected and all(v>=d for v,d in zip(expected,ctx.rc.increments));assert list(ctx.rc.increments)==list(ctx.native.arrays[5]);checks+=1
 ctx.set_history({});assert all(ctx.native.arrays[3][s]==ctx.rc.increments[s]+(0 if n in owner else ctx.penalties[s]) for s,n in enumerate(ctx.rc.fields['dest_ranks']));ctx.reset();assert list(ctx.native.arrays[3])==baseline and not ctx.history and not ctx.wire_owner_union
node=next(n for n in nodes if ctx.wire_lengths[n]);ctx.set_wire_owner_union({node});ctx.set_history({node:3})
def snapshot():return (list(ctx.native.arrays[3]),dict(ctx.history),ctx.wire_owner_union)
def throwing():
 yield node
 raise RuntimeError('injected owner iterator failure')
for call,exc in ((lambda:ctx.set_wire_owner_union({-1}),ValueError),(lambda:ctx.set_wire_owner_union({True}),ValueError),(lambda:ctx.set_wire_owner_union(throwing()),RuntimeError),(lambda:ctx.set_history({node:1<<100}),ValueError)):
 before=snapshot()
 try:call()
 except exc:pass
 else:raise AssertionError('invalid update accepted')
 assert snapshot()==before
# A simple physical witness charges exactly the channel nodes newly added to
# its NET union; discounts change search cost only, not delay increments.
before=snapshot();ctx.restore_wire_state({},());ctx.restore_wire_state(before[1],before[2]);assert snapshot()==before
ctx.reset();q=ctx.context[5][0];answer=ctx.query(q['source'],q['sink'],ctx.rc.scale//10**9,{})
assert answer['status']=='FOUND';slots={eid:s for s,eid in enumerate(ctx.rc.fields['edge_ids'])};path={q['source']};u=q['source']
for eid in answer['physical_edge_ids']:
 slot=slots[eid];u=ctx.rc.fields['dest_ranks'][slot];path.add(u)
owner=set(list(path)[::2]);ctx.set_wire_owner_union(owner);penalty=sum(ctx.penalties[slots[eid]] for eid in answer['physical_edge_ids'] if ctx.rc.fields['dest_ranks'][slots[eid]] not in owner);unit=F(ctx.weight_ns)*ctx.rc.scale/10**9;delta=sum(ctx.wire_lengths[n] for n in path-owner);assert penalty==unit*delta
out=ROOT/'experiments/owner_union_wire_context_contract_2026-10-07';out.mkdir(exist_ok=True);(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),helper_sha256=sha(ROOT/'tools/owner_union_wire_rc_context.py'),base_helper_sha256=sha(ROOT/'tools/wire_penalty_rc_context.py'),endpoint_sha256=sha(endpoint),transitions=checks,scope='40 actualgraph full-array owner/history algebra checks, reset, uint64 invalid/overflow and iterator-failure preservation; dynamiccost>=exactdelay, immutableincrements; simple actual physical witness penalty equals new NETunion channel wire. Caller must provide true NETunion; no complete staging/release/nativeQoR/concurrent publication proof.'),indent=2)+'\n');print('Owner-union wire context contract passed',checks,'transitions',flush=True)
