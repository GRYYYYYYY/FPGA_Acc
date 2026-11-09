"""Bounded online conflict allocation/staging adapter; same fixed twelve moves."""
import ctypes,json,time
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from online_conflict_core import shortest_delay,observe_conflict
from bounded_conflict_branch_core import bounded_conflict_branches
from owner_union_wire_rc_context import OwnerUnionWireRCContext as PersistentRCContext
from native_route_ledger_import import import_native_ledger
from pre_route_endpoints import sha
from fixed_connection_cap_allocation import allocate_budget
from owned_reverse_graph import OwnedReverseGraph
from exact_incremental_timing_dag import ExactTimingDAG
import connection_budget_owner_wire_staged_reroute as staging
import connection_budget_owner_wire_history32_engine as repair
import moved_history_repair_engine as engine
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_critical_release_budgets_2026-10-06';out=ROOT/'experiments/mux_owner_union_wire_fixed_cap_cohort_2026-10-07';predecessor=ROOT/'experiments/mux_bounded_branch_online_loop_2026-10-06';pr=json.loads((predecessor/'receipt.json').read_text());pv=json.loads((predecessor/'audit_summary.json').read_text());assert len(pr['rows'])==12 and pv['receipt_sha256']==sha(predecessor/'receipt.json');out.mkdir();protocol=json.loads((base/'protocol.json').read_text());rows=[];binary=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';engine.repair_moved_history=repair.repair_moved_history
sources=[Path(__file__),ROOT/'tools/fixed_connection_cap_allocation.py',ROOT/'tools/wire_penalty_rc_context.py',ROOT/'tools/owner_union_wire_rc_context.py',ROOT/'tools/owned_reverse_graph.py',ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.cpp',ROOT/'tools/exact_incremental_timing_dag.py',ROOT/'tools/bounded_conflict_branch_core.py',ROOT/'tools/online_conflict_core.py',ROOT/'tools/connection_budget_owner_wire_staged_reroute.py',ROOT/'tools/connection_budget_owner_wire_history32_engine.py',ROOT/'tools/single_scan_residual_frontier.py']
(out/'protocol.json').write_text(json.dumps(dict(predecessor_receipt_sha256=sha(predecessor/'receipt.json'),predecessor_audit_sha256=sha(predecessor/'audit_summary.json'),predecessor_complete=sum(r['status']=='COMPLETE_CANDIDATE' for r in pr['rows']),cases=protocol['cases'],base_receipt_sha256=sha(base/'receipt.json'),base_verification_sha256=sha(base/'verification.json'),sources={str(p):sha(p) for p in sources},binary_sha256=sha(binary),cache_payload_limit_bytes=128*1024*1024,certified_baseline_receipt_sha256=sha(ROOT/'experiments/mux_lazy_budget_cache_cohort_2026-10-06/receipt.json'),certified_baseline_evidence_sha256=sha(ROOT/'experiments/mux_lazy_budget_cache_cohort_2026-10-06/final_evidence.json'),owner_union_contract_sha256=sha(ROOT/'experiments/owner_union_wire_context_contract_2026-10-07/verification.json'),wire_penalty_weight_ns='1/100',wire_penalty_contract_sha256=sha(ROOT/'experiments/wire_penalty_context_contract_2026-10-07/verification.json'),policy='One fixed10ps per new destination channel-span unit outside explicitly supplied current NET union; retain exact RC cost/delay and quadratic history. Owner union captured in each query event and combined history/owner restoration required. No weight sweep/tuning; local incremental unique-wire objective, not global tree optimum. Exact delay caps unchanged; same raw/effective quadratic history. Fixed frozen12 cases; unchanged critical-release masks/planning-floor scores and branch/repair/search limits, single-scan repair. Expanded query caps fixed1ns; retained reporting budget=max(1ns,planning delay), reroute queries capped1ns. No NET-slack preparation/vector input or budget-envelope target certification. Planning-floor rejection is bounded model planning, not universal retained-delay necessity. Complete actual-delay DAG check and independent native FULLSTA quality gate mandatory; no publication. Timing-rejected complete candidates separate. Same max4attempts/max32queue/32repair/10000labels. Strategy change, not semantic parity; original floor/setup/native acceptance costs additional.'),indent=2)+'\n')
for case in protocol['cases']:
 w,i=case['width'],case['index'];work=out/f'w{w}_m{i}';work.mkdir();af=base/f'w{w}_m{i}.json';initial=json.loads(af.read_text());oldfile=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';a={**json.loads(oldfile.read_text()),**initial}
 if a['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':rows.append(dict(width=w,index=i,status='PRIOR_ALLOCATION_SKIP'));continue
 a['budgets_ns']={} # Fixed-cap allocation does not consume NET-slack vectors.

 begin=time.perf_counter();ctx=PersistentRCContext(case['old']);state=import_native_ledger(ctx,ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route');owned=OwnedReverseGraph(ctx.native.n,len(ctx.rc.fields['edge_ids']),ctx.native.ptrs[0],ctx.native.ptrs[1],ctx.native.ptrs[2],ctx.native.ptrs[5],binary);ctx.native.lib.rc_query=owned.bridge
 target=json.loads(Path(case['target']).read_text());queries=target['connections'];tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mapping=json.loads(mf.read_text());dag=ExactTimingDAG.from_native_metadata(tg,mapping,a,a['floor_ns'])
 def evaluate(b):
  return dag.update(b)
 cache={};allocations=[];attempts=[];target_cpd=F(a['target_cpd_ns']);priority=json.loads((ROOT/f'experiments/mux_old_timing_priority_2026-10-06/w{w}_priority.json').read_text());ranks={int(k):priority['net_rank_by_name'].get(name,1000000) for k,name in ctx.endpoint_metadata['net_names'].items()}
 phase_times={'allocate':[],'attempt':[],'observe':[],'native_query':[]}
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
  value,valid,budget,budget_policy,low=allocate_budget(floor,expanded,{int(cid):F(v) for cid,v in a['budgets_ns'].items()},target_cpd,restrictions,supported,evaluate)
  increase=sum(max(F(0),floor[int(cid)]-F(value)) for cid,value in a['floor_ns'].items())
  spec=dict(budget_policy=budget_policy,total_floor_increase_ns=str(increase),index=len(allocations),restrictions={str(k):sorted(v) for k,v in restrictions.items()},expanded=sorted(expanded),floor_ns={str(k):str(v) for k,v in floor.items()},budgets_ns={str(k):str(v) for k,v in budget.items()},floor_cpd_ns=str(value),budget_cpd_ns=str(evaluate(budget)) if valid else None,interpolation=None if low is None else str(low),valid=valid)
  allocations.append(spec)
  return ((value,increase),spec) if valid else None
 def attempt(restrictions,spec):
  expanded=set(spec['expanded']);nets={q['net_id'] for q in queries if q['connection_id'] in expanded};assert expanded=={q['connection_id'] for q in queries if q['net_id'] in nets};pair_bans={}
  for q in queries:
   if q['net_id'] in restrictions:pair_bans.setdefault((q['source'],q['sink']),set()).update(restrictions[q['net_id']])
  original_query=ctx.query;original_bind=ctx.bind_endpoints;old_budgets=(staging.BUDGETS,repair.BUDGETS);old_ranks=(staging.NET_PRIORITY,repair.NET_PRIORITY);history=dict(ctx.history);wire_owner=ctx.wire_owner_union;old_context=ctx.context;metadata=ctx.endpoint_metadata;other={n:ctx.native.other[n] for n in ctx.native.previous}
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
   assert ctx.wire_owner_union==wire_owner and ctx.context is old_context and ctx.endpoint_metadata is metadata and ctx.history==history and {n:ctx.native.other[n] for n in ctx.native.previous}==other
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
 model_gate=dict(status='NOT_COMPLETE')
 if result['status']=='COMPLETE_CANDIDATE':
  candidate=result['candidate'];actual={int(q['connection_id']):F(q['answer']['delay']*10**9,candidate['scale']) for q in candidate['records']};assert set(actual)=={int(k) for k in a['floor_ns']};actual_cpd=evaluate(actual);model_gate=dict(status='ACTUAL_MODEL_PASS_NATIVE_PENDING' if actual_cpd<=target_cpd else 'ACTUAL_MODEL_TIMING_REJECTED',actual_cpd_ns=str(actual_cpd),target_cpd_ns=str(target_cpd),scope='Old local-offset model hypothesis, not native STA or publication.')
 (work/'phase_times.json').write_text(json.dumps(dict(phases={name:dict(calls=len(values),seconds=sum(values),per_call_seconds=values) for name,values in phase_times.items()},scope='Single prospective profiled case; native_query nested inside attempt, never add both. Setup and serialization excluded from phase timers, loop includes setup. Per-query clock overhead and concurrent work, no matched speedup.'),indent=2)+'\n');file=work/'result.json';file.write_text(json.dumps(dict(initial_floor_seed_sha256=sha(af),fixed_cap_contract_sha256=sha(ROOT/'experiments/fixed_connection_cap_contract_2026-10-07/verification.json'),candidate_model_gate=model_gate,result=result,allocations=allocations,attempts=attempts),indent=2)+'\n');row=dict(width=w,index=i,status=(model_gate['status'] if result['status']=='COMPLETE_CANDIDATE' else result['status']),routing_status=result['status'],attempts=len(result['trace']),allocations=len(allocations),completed=result.get('candidate',{}).get('completed_connections'),loop_seconds=time.perf_counter()-begin,result_sha256=sha(file));rows.append(row);print(row,flush=True)
 cache_stats=(ctypes.c_uint64*6)();owned.lib.rc_graph_cache_stats.argtypes=[ctypes.c_uint64,ctypes.POINTER(ctypes.c_uint64)];owned.lib.rc_graph_cache_stats.restype=ctypes.c_int;assert owned.lib.rc_graph_cache_stats(owned.handle,cache_stats)==0
 (work/'cache_stats.json').write_text(json.dumps(dict(zip(['hits','misses','invalidations','evictions','payload_bytes','payload_limit_bytes'],map(int,cache_stats))),indent=2)+'\n')
 owned.close()
 assert all(sha(p)==h for p,h in case['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
