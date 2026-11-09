"""Two read-only probes of one native-seeded context; not stateful accepted updates."""
import json,time,hashlib
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from moved_budget_preflight import check
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_reused_budget_preflight_2026-10-06';out.mkdir();base=ROOT/'experiments/mux_live_placement_updates_2026-10-06';budgetroot=ROOT/'experiments/mux_connection_budgets_2026-10-06';cases=[]
for w in (8,16,32):
 paths=[base/f'w{w}/original_endpoints.json',base/f'w{w}/swapped_endpoints.json',budgetroot/f'w{w}.json',ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route'];cases.append(dict(width=w,inputs={str(p):sha(p)for p in paths}))
(out/'protocol.json').write_text(json.dumps(dict(cases=cases,sources={str(p):sha(p)for p in (Path(__file__),ROOT/'tools/moved_budget_preflight.py')},scope='Two repeated speculative checks on one old native-seeded context, no accepted-state transition/coldfallback timing. Context/nativeledger setup excluded probe timings but archived. Both success/rejection and exceptional exits must restore endpoints/history/demand/nativearrays/ledger.'),indent=2)+'\n');rows=[]
def fingerprint(ctx,state):
 h=hashlib.sha256()
 for a in ctx.native.arrays+[ctx.native.other]:h.update(a.tobytes())
 return dict(buffers=h.hexdigest(),history=dict(ctx.history),previous=sorted(ctx.native.previous),records=repr(state.records),unions=repr(state.unions),ledger=repr(state.ledger),parents=repr(state.parents))
for case in cases:
 w=case['width'];begin=time.perf_counter();ctx=PersistentRCContext(base/f'w{w}/original_endpoints.json');state=import_native_ledger(ctx,ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route');setup=time.perf_counter()-begin;spec=json.loads((budgetroot/f'w{w}.json').read_text());budgets={int(c):int(Fraction(ns)*ctx.rc.scale/10**9)for c,ns in spec['budgets_ns'].items()};before=fingerprint(ctx,state);context=ctx.context;metadata=ctx.endpoint_metadata;probes=[]
 for index in range(2):
  begin=time.perf_counter();result=check(ctx,base/f'w{w}/swapped_endpoints.json',budgets);seconds=time.perf_counter()-begin;assert ctx.context is context and ctx.endpoint_metadata is metadata and fingerprint(ctx,state)==before;probes.append(dict(seconds=seconds,result=result))
 assert probes[0]['result']==probes[1]['result']
 # Unknown CID is rejected after temporary binding; verify finally restores state.
 try:check(ctx,base/f'w{w}/swapped_endpoints.json',{**budgets,999999999:1})
 except ValueError:pass
 else:raise AssertionError('unknown connection accepted')
 assert ctx.context is context and ctx.endpoint_metadata is metadata and fingerprint(ctx,state)==before
 work=out/f'w{w}.json';work.write_text(json.dumps(dict(probes=probes,restored_endpoint_identity=True,restored_all_buffers_history_ledger=True,exceptional_exit_restored=True),indent=2)+'\n');row=dict(width=w,setup_seconds=setup,probe_seconds=[p['seconds']for p in probes],status=probes[0]['result']['status'],sha256=sha(work));rows.append(row);assert all(sha(p)==h for p,h in case['inputs'].items());print(row,flush=True)
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
