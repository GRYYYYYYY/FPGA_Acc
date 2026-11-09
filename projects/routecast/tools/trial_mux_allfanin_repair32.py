"""Fixed full cohort constrained reroute; all allocation outcomes retained."""
import ctypes,json,time
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
import connection_budget_staged_reroute_v2 as staging
import connection_budget_repair32_engine as replacement
import moved_history_repair_engine as engine
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';p=json.loads((parent/'protocol.json').read_text());p['rows']=json.loads((parent/'receipt.json').read_text())['rows'];out=ROOT/'experiments/mux_allfanin_repair32_2026-10-06';out.mkdir();binary=ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so';engine.repair_moved_history=replacement.repair_moved_history
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],allocations=p['rows'],parent_protocol_sha256=sha(parent/'protocol.json'),parent_receipt_sha256=sha(parent/'receipt.json'),binary_sha256=sha(binary),sources={str(f):sha(f)for f in(Path(__file__),ROOT/'tools/connection_budget_staged_reroute_v2.py',ROOT/'tools/connection_budget_repair32_engine.py')},policy='All12 outcomes retained,7 constructed allfanin vectors searched;5 diagnostic allocation failures explicit notsubmitted. SameoldwholeNETpriority,target-bound ordering,10000labels/max32releases; only repair limit changed from frozen max4 trial. Floor/budgetpreparation excluded stage timings and archived separately; not total gain.'),indent=2)+'\n');rows=[];last=None
for c,a in zip(p['cases'],p['rows']):
 w,i=c['width'],c['index'];work=out/f'w{w}_m{i}';work.mkdir();allocation=parent/f'w{w}_m{i}.json';assert sha(allocation)==a['sha256'];spec=json.loads(allocation.read_text())
 if spec['status']!='ALLFANIN_VECTOR_CONSTRUCTED':row=dict(width=w,index=i,status='ALLOCATION_NOT_SUBMITTED',failure=spec['status'])
 else:
  if w!=last:
   ctx=PersistentRCContext(c['old']);state=import_native_ledger(ctx,ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route');signature=ctx.native.lib.rc_query.argtypes;ctx.native.lib=ctypes.CDLL(str(binary));ctx.native.lib.rc_query.argtypes=signature;ctx.native.lib.rc_query.restype=ctypes.c_int;last=w
  budgets={int(cid):min(int(Fraction(ns)*ctx.rc.scale/10**9),ctx.rc.scale//10**9)for cid,ns in spec['budgets_ns'].items()};staging.BUDGETS=budgets;replacement.BUDGETS=budgets;priority=json.loads((ROOT/f'experiments/mux_old_timing_priority_2026-10-06/w{w}_priority.json').read_text());ranks={int(k):priority['net_rank_by_name'].get(name,1000000)for k,name in ctx.endpoint_metadata['net_names'].items()};staging.NET_PRIORITY=ranks;replacement.NET_PRIORITY=ranks;begin=time.perf_counter();update=staging.stage_reroute_with_repair(state,c['target']);seconds=time.perf_counter()-begin;candidate=update['repair']or update['incremental'];(work/'update.json').write_text(json.dumps(update,indent=2)+'\n');file=work/'prediction.json';file.write_text(json.dumps(candidate,indent=2)+'\n');row=dict(width=w,index=i,status=candidate['status'],completed=candidate['completed_connections'],required=candidate['required_connections'],failure=candidate['failure'],stage_seconds=seconds,prediction_sha256=sha(file))
 rows.append(row);assert all(sha(f)==h for f,h in c['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(row,flush=True)
