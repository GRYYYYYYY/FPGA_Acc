"""Prospective moved-endpoint minimum-delay preflight, all frozen mux cases."""
import heapq,json,time
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_budget_preflight_2026-10-06';out.mkdir();base=ROOT/'experiments/mux_live_placement_updates_2026-10-06';budgetroot=ROOT/'experiments/mux_connection_budgets_2026-10-06';cases=[]
for w in (8,16,32):
 paths=[base/f'w{w}/original_endpoints.json',base/f'w{w}/swapped_endpoints.json',budgetroot/f'w{w}.json'];cases.append(dict(width=w,inputs={str(p):sha(p)for p in paths}))
(out/'protocol.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),cases=cases,policy='All affected wholeNET budgeted connections checked before routing; positive-capacity graph, zero otherNET demand; full integer Dijkstra per distinct SOURCE. Any infeasible connection rejects hard-budget candidate and requests native cold route. No budget relaxation or partial publication. Context parsing and lower-bound work measured separately.'),indent=2)+'\n');rows=[]
for case in cases:
 w=case['width'];begin=time.perf_counter();ctx=PersistentRCContext(base/f'w{w}/original_endpoints.json');affected=ctx.bind_endpoints(base/f'w{w}/swapped_endpoints.json');context_s=time.perf_counter()-begin;spec=json.loads((budgetroot/f'w{w}.json').read_text());budgets={int(cid):int(Fraction(ns)*ctx.rc.scale/10**9)for cid,ns in spec['budgets_ns'].items()};queries=[q for q in ctx.context[5]if q['connection_id']in affected['affected_complete_net_connection_ids']and q['connection_id']in budgets];f=ctx.rc.fields;cache={};lower_start=time.perf_counter();observations=[]
 for q in queries:
  source=q['source']
  if source not in cache:
   dist={source:ctx.rc.initial(source)} if f['capacities'][source]>0 else {};heap=[(dist[source],source)]if dist else [];expanded=0
   while heap:
    delay,node=heapq.heappop(heap)
    if dist[node]!=delay:continue
    expanded+=1
    for slot in range(f['row_offsets'][node],f['row_offsets'][node+1]):
     sink=f['dest_ranks'][slot]
     if not f['capacities'][sink]:continue
     nd=delay+ctx.rc.increments[slot]
     if sink not in dist or nd<dist[sink]:dist[sink]=nd;heapq.heappush(heap,(nd,sink))
   cache[source]=(dist,expanded)
  dist,_=cache[source];minimum=dist.get(q['sink']);budget=budgets[q['connection_id']];observations.append(dict(query=q,budget_units=budget,minimum_units=minimum,feasible=minimum is not None and minimum<=budget,budget_ns=spec['budgets_ns'][str(q['connection_id'])],minimum_ns=str(Fraction(minimum*10**9,ctx.rc.scale))if minimum is not None else None))
 lower_s=time.perf_counter()-lower_start;violations=[o for o in observations if not o['feasible']];file=out/f'w{w}.json';file.write_text(json.dumps(dict(scale=ctx.rc.scale,affected=affected,observations=observations),indent=2)+'\n');row=dict(width=w,budgeted_affected_connections=len(queries),infeasible_connections=len(violations),distinct_sources=len(cache),context_bind_seconds=context_s,preflight_seconds=lower_s,status='REJECT_BUDGET_CANDIDATE_USE_NATIVE_COLD'if violations else'BUDGET_PREFLIGHT_PASS_NOT_ROUTE_PROOF',observation_sha256=sha(file));rows.append(row);assert all(sha(p)==h for p,h in case['inputs'].items());print(row,flush=True)
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
