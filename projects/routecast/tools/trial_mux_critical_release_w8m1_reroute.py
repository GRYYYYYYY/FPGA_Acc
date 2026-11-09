"""Fixed full cohort constrained reroute; all allocation outcomes retained."""
import ctypes,json,time
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
import connection_budget_staged_reroute_v2 as staging
import connection_budget_priority32_engine as replacement
import moved_history_repair_engine as engine
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_critical_release_budgets_2026-10-06';p=json.loads((parent/'protocol.json').read_text());p['rows']=json.loads((parent/'receipt.json').read_text())['rows'];chosen=[j for j,c in enumerate(p['cases']) if (c['width'],c['index'])==(8,1)];p['cases']=[p['cases'][j] for j in chosen];p['rows']=[p['rows'][j] for j in chosen];out=ROOT/'experiments/mux_critical_release_w8m1_reroute_2026-10-06';out.mkdir();binary=ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so';engine.repair_moved_history=replacement.repair_moved_history
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],allocations=p['rows'],parent_protocol_sha256=sha(parent/'protocol.json'),parent_receipt_sha256=sha(parent/'receipt.json'),binary_sha256=sha(binary),sources={str(f):sha(f)for f in(Path(__file__),ROOT/'tools/connection_budget_staged_reroute_v2.py',ROOT/'tools/connection_budget_priority32_engine.py')},policy='Focused newly enabled w8m1 case after independent all12 initial release-rule verification. SameoldwholeNETpriority,target-bound ordering,10000labels/max32releases; critical-path retained-release budgets; expanded wholeNET staging release; accumulated perNET exclusions in every query including relaxed witnesses; shared endpoint pairs receive union of bans; retrospective allocation; max32 priority repair. Floor/budgetpreparation excluded stage timings and archived separately; not total gain.'),indent=2)+'\n');rows=[];last=None
for c,a in zip(p['cases'],p['rows']):
 w,i=c['width'],c['index'];work=out/f'w{w}_m{i}';work.mkdir();allocation=parent/f'w{w}_m{i}.json'
 if a['status']=='ALLOCATION_NOT_SUBMITTED':
  rows.append(dict(width=w,index=i,status='ALLOCATION_NOT_SUBMITTED',failure='PRIOR_ALLOCATION_SKIP'));continue
 assert sha(allocation)==a['sha256'];spec=json.loads(allocation.read_text());spec['restrictions']={}
 if spec['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':row=dict(width=w,index=i,status='ALLOCATION_NOT_SUBMITTED',failure=spec['status'])
 else:
  if w!=last:
   ctx=PersistentRCContext(c['old']);state=import_native_ledger(ctx,ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route');signature=ctx.native.lib.rc_query.argtypes;ctx.native.lib=ctypes.CDLL(str(binary));ctx.native.lib.rc_query.argtypes=signature;ctx.native.lib.rc_query.restype=ctypes.c_int;last=w
  target=json.loads(Path(c['target']).read_text());pair_bans={};expanded=set(spec['expanded_connection_ids']);expanded_nets={q['net_id'] for q in target['connections'] if q['connection_id'] in expanded};calls=[]
  assert expanded=={q['connection_id'] for q in target['connections'] if q['net_id'] in expanded_nets}
  for q in target['connections']:
   bans=spec['restrictions'].get(str(q['net_id']),[])
   if bans:pair_bans.setdefault((q['source'],q['sink']),set()).update(bans)
  base_query=ctx.query;base_bind=ctx.bind_endpoints
  def avoid_query(source,sink,budget,other,max_labels=10000):
   demand=dict(other);bans=pair_bans.get((source,sink),set())
   for node in bans:demand[node]=ctx.rc.fields['capacities'][node]
   answer=base_query(source,sink,budget,demand,max_labels=max_labels);calls.append(dict(source=source,sink=sink,forbidden=sorted(bans),status=answer['status']))
   return answer
  def expanded_bind(path):
   affected=base_bind(path);assert set(affected['affected_net_ids'])<=expanded_nets
   affected['affected_net_ids']=sorted(expanded_nets);affected['affected_complete_net_connection_ids']=sorted(expanded)
   return affected
  ctx.query=avoid_query;ctx.bind_endpoints=expanded_bind
  budgets={int(cid):min(int(Fraction(ns)*ctx.rc.scale/10**9),ctx.rc.scale//10**9)for cid,ns in spec['budgets_ns'].items()};staging.BUDGETS=budgets;replacement.BUDGETS=budgets;priority=json.loads((ROOT/f'experiments/mux_old_timing_priority_2026-10-06/w{w}_priority.json').read_text());ranks={int(k):priority['net_rank_by_name'].get(name,1000000)for k,name in ctx.endpoint_metadata['net_names'].items()};staging.NET_PRIORITY=ranks;replacement.NET_PRIORITY=ranks;begin=time.perf_counter();update=staging.stage_reroute_with_repair(state,c['target']);seconds=time.perf_counter()-begin;ctx.query=base_query;ctx.bind_endpoints=base_bind;candidate=update['repair']or update['incremental'];(work/'avoid_queries.json').write_text(json.dumps(dict(restrictions=spec['restrictions'],expanded_connection_ids=sorted(expanded),pair_bans=[dict(source=k[0],sink=k[1],forbidden=sorted(v)) for k,v in sorted(pair_bans.items())],calls=calls),indent=2)+'\n');(work/'update.json').write_text(json.dumps(update,indent=2)+'\n');file=work/'prediction.json';file.write_text(json.dumps(candidate,indent=2)+'\n');row=dict(width=w,index=i,status=candidate['status'],completed=candidate['completed_connections'],required=candidate['required_connections'],failure=candidate['failure'],stage_seconds=seconds,prediction_sha256=sha(file))
 rows.append(row);assert all(sha(f)==h for f,h in c['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(row,flush=True)
