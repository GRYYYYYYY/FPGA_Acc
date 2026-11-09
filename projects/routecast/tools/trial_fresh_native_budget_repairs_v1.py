"""Discover all failures from a complete raw native route, attempt each in order."""
import json,sys,time
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from native_bounded_wire_search_v1 import NativeBoundedSearch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
started=time.perf_counter();case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=Path(case['target']);meta=json.loads(ep.read_text());route=R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route';bp=Path(case['budget']);budget=json.loads(bp.read_text())
bindings={**closure([Path(__file__)]),str(ep):sha(ep),str(route):sha(route),str(bp):sha(bp)}
graph,digest,nodes,f,rc,queries=load_endpoints(ep);bindings[str(graph)]=digest
state,rows,ledger=load_complete(route,meta,nodes,f,rc);native=NativeBoundedSearch(rc,{});bindings.update(native.bindings)
byid={q['connection_id']:q for q in queries};delay={x['connection_id']:x['delay_integer'] for x in rows};limits={cid:F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))*rc.scale/10**9 for cid in byid}
violations=sorted(cid for cid in byid if delay[cid]>limits[cid]);D=R/'experiments/fresh_native_budget_repairs_v1_2026-10-08';D.mkdir(exist_ok=False)
protocol=dict(bindings=bindings,initial_complete_connections=len(state),attempt_order=violations,max_labels=len(f['edge_ids'])+1,policy='Import all raw post-resume native demands/physical paths afresh, discover budget violations, attempt ALL in ascending cid. Zero-objective exact Pareto reduces to min-delay Dijkstra; nonnegative increments, at most edges+1 created labels. Other owners and retained sameNET parents fixed, no whole NET released. Exhaustion means constrained budget path not found; no unconstrained infeasibility inferred. Original budgets never changed. Component starts at provided complete native route; excludes production of that route/endpoint/budget and downstream owners/wire/VPR/audits.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');events=[];slots={eid:i for i,eid in enumerate(f['edge_ids'])}
for cid in violations:
 q=byid[cid];net=q['net_id'];kept,fixed=ledger.view(cid);outside=ledger.occupancy.copy();outside.subtract(ledger.nodes[net].keys());limit=limits[cid];ceiling=limit.numerator//limit.denominator;tick=time.perf_counter()
 answer=native.query(q['source'],q['sink'],ceiling,outside,kept,fixed,max_labels=len(f['edge_ids'])+1,cost_limit_exclusive=1)
 event=dict(connection_id=cid,query=q,old_path=[list(x) for x in ledger.state[cid]],old_delay_integer=delay[cid],budget_integer_ceiling=ceiling,search=answer,search_seconds=time.perf_counter()-tick,status='RETAIN_'+answer['status'])
 if answer['status']=='FOUND':
  u=q['source'];path=[(u,None)]
  for eid in answer['physical_edge_ids']:
   slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];u=f['dest_ranks'][slot];path.append((u,f['switch_ids'][slot]))
  assert u==q['sink'] and answer['cost']==0;ledger.replace(cid,path);delay[cid]=answer['delay'];event.update(status='COMMIT',new_path=[list(x) for x in path])
 events.append(event);print(cid,event['status'],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),scale=rc.scale,initial_rows=rows,initial_budget_violation_ids=violations,events=events,state={str(cid):[list(x) for x in path] for cid,path in ledger.state.items()},complete_connections=len(ledger.state),final_budget_violation_ids=sorted(cid for cid in byid if delay[cid]>limits[cid]),wirelength=sum(ledger.wire.values()),native_calls=native.native_calls,fallback_calls=native.fallback_calls,search_seconds=sum(e['search_seconds'] for e in events),component_elapsed_seconds=time.perf_counter()-started,scope='Fresh budget stage only from given complete raw native route, not whole workflow. Physical/RC/budget replay and comparison to historical repair still required; no native VPR/STA or original HDL equivalence claim.')
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');native.close()
