"""Bounded online conflict allocation/staging adapter; same fixed twelve moves."""
import ctypes,json,time
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from online_conflict_core import shortest_delay,observe_conflict
from bounded_conflict_branch_core import bounded_conflict_branches
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from pre_route_endpoints import sha
from exact_incremental_timing_dag import ExactTimingDAG
import connection_budget_staged_reroute_v2 as staging
import connection_budget_quadratic_history32_engine as repair
import moved_history_repair_engine as engine
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_critical_release_budgets_2026-10-06';out=ROOT/'experiments/mux_net_slack_query_profile_2026-10-06';predecessor=ROOT/'experiments/mux_bounded_branch_online_loop_2026-10-06';pr=json.loads((predecessor/'receipt.json').read_text());pv=json.loads((predecessor/'audit_summary.json').read_text());assert len(pr['rows'])==12 and pv['receipt_sha256']==sha(predecessor/'receipt.json');slack_root=ROOT/'experiments/mux_net_slack_budgets_2026-10-06';sr=json.loads((slack_root/'receipt.json').read_text());sv=json.loads((slack_root/'verification.json').read_text());assert len(sr['rows'])==12 and sv['receipt_sha256']==sha(slack_root/'receipt.json');out.mkdir();protocol=json.loads((base/'protocol.json').read_text());protocol['cases']=[c for c in protocol['cases'] if (c['width'],c['index'])==(32,2)];rows=[];binary=ROOT/'experiments/mux_old_priority_repair_2026-10-06/search.so';engine.repair_moved_history=repair.repair_moved_history
sources=[Path(__file__),ROOT/'tools/exact_incremental_timing_dag.py',ROOT/'tools/bounded_conflict_branch_core.py',ROOT/'tools/online_conflict_core.py',ROOT/'tools/connection_budget_staged_reroute_v2.py',ROOT/'tools/connection_budget_quadratic_history32_engine.py']
(out/'protocol.json').write_text(json.dumps(dict(net_slack_receipt_sha256=sha(slack_root/'receipt.json'),net_slack_verification_sha256=sha(slack_root/'verification.json'),predecessor_receipt_sha256=sha(predecessor/'receipt.json'),predecessor_audit_sha256=sha(predecessor/'audit_summary.json'),predecessor_complete=sum(r['status']=='COMPLETE_CANDIDATE' for r in pr['rows']),cases=protocol['cases'],base_receipt_sha256=sha(base/'receipt.json'),base_verification_sha256=sha(base/'verification.json'),sources={str(p):sha(p) for p in sources},binary_sha256=sha(binary),policy='Single width32m2 stage timing diagnostic, not full12cohort run. Exact incremental timing evaluator; allocation/search policy unchanged. Empty exclusions, no archived conflict input. Primary floorCPD/secondary total positive floor increase/order selection unchanged from frozen score predecessor. Quadratic history and score policy unchanged. Allocation retained from frozen preserved-budget predecessor: for nonempty same-run exclusions preserve INITIAL budgets raised to conditional floors when fullDAG target and expanded1ns caps hold; otherwise original uniform allocation. Initial empty floor/release set identical; budget vector widened. No archived conflict probe input. All original12 cases retained, including4 initialskips. ONLY budget change: independently verified ascendingNET wholeNET slack vector for initial budget and subsequent preservation baseline. No cold input. Control retained: breadth-first alternative branches, exact constraint-state dedup, max32 queued states, same score/order within depth, parent-child monotone exclusions. Chronological siblings need not accumulate exclusions. Success criterion: more complete native-validated candidates than frozen branch predecessor0/8; includes budget preparation cost separately; partial-count increases not acceptance. Max4 candidate attempts, max16 restricted NETs/32 exclusions, each attempt priority32 repairs/10000labels. Full oldDAG allocation24-step interpolation. Exact relaxed Dijkstra setup/option work included loop time, critical retained-NET release initialization excluded and independently archived; no cold-route oracle input. Synchronous candidate staging, no publication or native STA acceptance.'),indent=2)+'\n')
for case in protocol['cases']:
 w,i=case['width'],case['index'];work=out/f'w{w}_m{i}';work.mkdir();af=base/f'w{w}_m{i}.json';initial=json.loads(af.read_text());oldfile=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';a={**json.loads(oldfile.read_text()),**initial}
 if a['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':rows.append(dict(width=w,index=i,status='PRIOR_ALLOCATION_SKIP'));continue
 slack_root=ROOT/'experiments/mux_net_slack_budgets_2026-10-06';slack_file=slack_root/f'w{w}_m{i}.json';slack=json.loads(slack_file.read_text());slack_verification=json.loads((slack_root/f'w{w}_m{i}_verification.json').read_text());assert slack_verification['result_sha256']==sha(slack_file) and slack['base_sha256']==sha(af);assert slack['expanded_connection_ids']==a['expanded_connection_ids'];a['budgets_ns']=slack['budgets_ns']
 begin=time.perf_counter();ctx=PersistentRCContext(case['old']);state=import_native_ledger(ctx,ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route');signature=ctx.native.lib.rc_query.argtypes;ctx.native.lib=ctypes.CDLL(str(binary));ctx.native.lib.rc_query.argtypes=signature;ctx.native.lib.rc_query.restype=ctypes.c_int
 target=json.loads(Path(case['target']).read_text());queries=target['connections'];tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mapping=json.loads(mf.read_text());dag=ExactTimingDAG.from_native_metadata(tg,mapping,a,a['floor_ns'])
 def evaluate(b):
  return dag.update(b)
 cache={};allocations=[];attempts=[];target_cpd=F(a['target_cpd_ns']);priority=json.loads((ROOT/f'experiments/mux_old_timing_priority_2026-10-06/w{w}_priority.json').read_text());ranks={int(k):priority['net_rank_by_name'].get(name,1000000) for k,name in ctx.endpoint_metadata['net_names'].items()}
 phase_times={'allocate':[],'attempt':[],'observe':[],'native_query':[]}
 query_times={'set_other':[],'rc_query':[],'path_validation':[]}
 def instrument(name,callback):
  def wrapped(*args,**kwargs):
   start=time.perf_counter()
   try:return callback(*args,**kwargs)
   finally:query_times[name].append(time.perf_counter()-start)
  return wrapped
 ctx.native.set_other=instrument('set_other',ctx.native.set_other)
 ctx.native.lib.rc_query=instrument('rc_query',ctx.native.lib.rc_query)
 ctx.rc.path=instrument('path_validation',ctx.rc.path)
 def allocate(restrictions):
  floor={int(cid):F(x) for cid,x in a['floor_ns'].items()};expanded=set(a['expanded_connection_ids']);supported=True
  for q in queries:
   net=q['net_id']
   if net not in restrictions:continue
   expanded.add(q['connection_id']);key=(q['source'],tuple(sorted(restrictions[net])))
   if key not in cache:cache[key]=shortest_delay(ctx,q['source'],q['sink'],set(key[1]))
   minimum=cache[key]['distances'].get(q['sink'])
   if minimum is None:supported=False;continue
   floor[q['connection_id']]=max(floor[q['connection_id']],F(minimum*10**9,ctx.rc.scale))
  dag.update(floor,commit=True)
  value=evaluate(floor);valid=supported and value<=target_cpd and all(floor[cid]<=1 for cid in expanded);budget={};low=F(0)
  if valid:
   budget=dict(floor);high=F(1)
   for _ in range(24):
    mid=(low+high)/2;trial={cid:v+mid*(1-v) if cid in expanded else v for cid,v in floor.items()}
    if evaluate(trial)<=target_cpd:budget=trial;low=mid
    else:high=mid
  budget_policy='UNIFORM_INTERPOLATION'
  if valid and not restrictions:
   budget={int(cid):F(v) for cid,v in a['budgets_ns'].items()};assert evaluate(budget)<=target_cpd and all(floor[cid]<=budget[cid]<=1 for cid in expanded);budget_policy='INITIAL_NET_SLACK_VECTOR'
  if valid and restrictions:
   preserved={cid:max(F(a['budgets_ns'][str(cid)]),minimum) for cid,minimum in floor.items()}
   if all(preserved[cid]<=1 for cid in expanded) and evaluate(preserved)<=target_cpd:
    budget=preserved;budget_policy='PRESERVE_INITIAL_WITH_CONDITIONAL_FLOORS'
  increase=sum(max(F(0),floor[int(cid)]-F(value)) for cid,value in a['floor_ns'].items())
  spec=dict(budget_policy=budget_policy,total_floor_increase_ns=str(increase),index=len(allocations),restrictions={str(k):sorted(v) for k,v in restrictions.items()},expanded=sorted(expanded),floor_ns={str(k):str(v) for k,v in floor.items()},budgets_ns={str(k):str(v) for k,v in budget.items()},floor_cpd_ns=str(value),budget_cpd_ns=str(evaluate(budget)) if valid else None,interpolation=str(low),valid=valid)
  allocations.append(spec)
  return ((value,increase),spec) if valid else None
 def attempt(restrictions,spec):
  expanded=set(spec['expanded']);nets={q['net_id'] for q in queries if q['connection_id'] in expanded};assert expanded=={q['connection_id'] for q in queries if q['net_id'] in nets};pair_bans={}
  for q in queries:
   if q['net_id'] in restrictions:pair_bans.setdefault((q['source'],q['sink']),set()).update(restrictions[q['net_id']])
  original_query=ctx.query;original_bind=ctx.bind_endpoints;old_budgets=(staging.BUDGETS,repair.BUDGETS);old_ranks=(staging.NET_PRIORITY,repair.NET_PRIORITY);history=dict(ctx.history);old_context=ctx.context;metadata=ctx.endpoint_metadata;other={n:ctx.native.other[n] for n in ctx.native.previous}
  def query(source,sink,budget,demand,max_labels=10000):
   demand=dict(demand)
   for node in pair_bans.get((source,sink),()):demand[node]=ctx.rc.fields['capacities'][node]
   query_start=time.perf_counter()
   try:return original_query(source,sink,budget,demand,max_labels=max_labels)
   finally:phase_times['native_query'].append(time.perf_counter()-query_start)
  def bind(path):
   changed=original_bind(path);assert set(changed['affected_net_ids'])<=nets;changed['affected_net_ids']=sorted(nets);changed['affected_complete_net_connection_ids']=sorted(expanded);return changed
  try:
   ctx.query=query;ctx.bind_endpoints=bind;budgets={int(cid):min(int(F(value)*ctx.rc.scale/10**9),ctx.rc.scale//10**9) for cid,value in spec['budgets_ns'].items()};staging.BUDGETS=repair.BUDGETS=budgets;staging.NET_PRIORITY=repair.NET_PRIORITY=ranks
   update=staging.stage_reroute_with_repair(state,case['target']);candidate=update['repair'] or update['incremental'];attempts.append(dict(allocation_index=spec['index'],update=update));return candidate
  finally:
   ctx.query=original_query;ctx.bind_endpoints=original_bind;staging.BUDGETS,repair.BUDGETS=old_budgets;staging.NET_PRIORITY,repair.NET_PRIORITY=old_ranks
   assert ctx.context is old_context and ctx.endpoint_metadata is metadata and ctx.history==history and {n:ctx.native.other[n] for n in ctx.native.previous}==other
 def observe(candidate,restrictions,spec):
  context=ctx.context;metadata=ctx.endpoint_metadata
  try:
   ctx.bind_endpoints(case['target']);cid=candidate['failure']['query']['connection_id'];budget=min(int(F(spec['budgets_ns'][str(cid)])*ctx.rc.scale/10**9),ctx.rc.scale//10**9);return observe_conflict(ctx,candidate,restrictions,budget)
  finally:ctx.context=context;ctx.endpoint_metadata=metadata
 def timed(name,callback):
  def wrapped(*args):
   start=time.perf_counter()
   try:return callback(*args)
   finally:phase_times[name].append(time.perf_counter()-start)
  return wrapped
 result=bounded_conflict_branches({},timed('attempt',attempt),timed('observe',observe),timed('allocate',allocate),max_attempts=4,max_frontier=32);
 (work/'query_times.json').write_text(json.dumps(dict(phases={name:dict(calls=len(values),seconds=sum(values),per_call_seconds=values) for name,values in query_times.items()},scope='set_other includes resets outside ctx.query; rc_query times ctypes native call only; path_validation includes every native wrapper successful witness. Nested measurements, not additive with outer stage/query totals.'),indent=2)+'\n');
 (work/'phase_times.json').write_text(json.dumps(dict(phases={name:dict(calls=len(values),seconds=sum(values),per_call_seconds=values) for name,values in phase_times.items()},scope='Single prospective profiled case; native_query nested inside attempt, never add both. Setup and serialization excluded from phase timers, loop includes setup. Per-query clock overhead and concurrent work, no matched speedup.'),indent=2)+'\n');file=work/'result.json';file.write_text(json.dumps(dict(initial_budget_sha256=sha(slack_file),initial_budget_verification_sha256=sha(slack_root/f'w{w}_m{i}_verification.json'),result=result,allocations=allocations,attempts=attempts),indent=2)+'\n');row=dict(width=w,index=i,status=result['status'],attempts=len(result['trace']),allocations=len(allocations),completed=result.get('candidate',{}).get('completed_connections'),loop_seconds=time.perf_counter()-begin,result_sha256=sha(file));rows.append(row);print(row,flush=True)
 assert all(sha(p)==h for p,h in case['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
