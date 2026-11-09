"""Transport/history transaction checks on a real authenticated graph."""
import json
from pathlib import Path
from fractions import Fraction as F
from wire_penalty_rc_context import WirePenaltyRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];p=json.loads((ROOT/'experiments/mux_fixed_connection_cap_cohort_2026-10-07/protocol.json').read_text());case=p['cases'][0];ctx=WirePenaltyRCContext(case['old']);baseline=list(ctx.native.arrays[3]);assert baseline==[v+p for v,p in zip(ctx.rc.increments,ctx.penalties)];node=next(n for n in ctx.destination_slots if ctx.wire_lengths[n]);ctx.set_history({node:3});assert all(ctx.native.arrays[3][s]==ctx.rc.increments[s]*4+ctx.penalties[s] for s in ctx.destination_slots[node]);ctx.reset();assert list(ctx.native.arrays[3])==baseline and ctx.history=={}
for history in ({-1:1},{node:-1},{node:True},{node:1<<100}):
 before=list(ctx.native.arrays[3]);old=dict(ctx.history)
 try:ctx.set_history(history)
 except ValueError:pass
 else:raise AssertionError('invalid/overflow history accepted')
 assert list(ctx.native.arrays[3])==before and ctx.history==old
zero=WirePenaltyRCContext(case['old'],F(0));assert list(zero.native.arrays[3])==list(zero.rc.increments)
out=ROOT/'experiments/wire_penalty_context_contract_2026-10-07';out.mkdir(exist_ok=True);(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),helper_sha256=sha(ROOT/'tools/wire_penalty_rc_context.py'),endpoint_sha256=sha(case['old']),weight_ns=str(ctx.weight_ns),edges=len(ctx.penalties),scope='Actual graph exact cost transport/inc+fixed destination channel-span penalty, effective-history update/reset, invalid/overflow rejection before mutation, zero-weight cost equivalence. No path/native QoR or performance claim; unique perNET shared-wire length not modeled by static edge penalty.'),indent=2)+'\n');print('Wire penalty context contract passed',flush=True)
