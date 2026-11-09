"""Discover all failures from a complete raw native route, attempt each in order."""
import json,sys,time
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from native_bounded_wire_search_v1 import NativeBoundedSearch
from exact_integer_global_timing_v2 import ExactGlobalTiming
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
started=time.perf_counter();case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=Path(case['target']);meta=json.loads(ep.read_text());route=R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route';bp=Path(case['budget']);budget=json.loads(bp.read_text())
bindings={**closure([Path(__file__)]),str(ep):sha(ep),str(route):sha(route),str(bp):sha(bp)}
graph,digest,nodes,f,rc,queries=load_endpoints(ep);bindings[str(graph)]=digest
state,rows,ledger=load_complete(route,meta,nodes,f,rc);native=NativeBoundedSearch(rc,{});bindings.update(native.bindings)
byid={q['connection_id']:q for q in queries};delay={x['connection_id']:x['delay_integer'] for x in rows};limits={cid:F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))*rc.scale/10**9 for cid in byid}

previous=R/'experiments/fresh_native_budget_repairs_v1_2026-10-08';vp=previous/'verification.json';v=json.loads(vp.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp)
br=previous/'receipt.json';base=json.loads(br.read_text());bindings[str(br)]=sha(br);state={int(cid):tuple(tuple(x) for x in path) for cid,path in base['state'].items()}
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
ledger=SharedTreeLedger(state,byid,f['capacities'],ledger.length);delays={x['connection_id']:F(x['delay_seconds']) for x in v['rows']}
files=[R/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json',R/'experiments/mux_full_timing_rr_2026-10-06/w32.json',R/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json']
for path in files:bindings[str(path)]=sha(path)
tg,mapping,allocation=[json.loads(path.read_text()) for path in files];assert allocation['graph_sha256']==sha(files[0])==mapping['timing_graph_sha256'] and allocation['mapping_sha256']==sha(files[1])
model=ExactGlobalTiming(tg,mapping,allocation,rc.scale,F(1000)/10**9,delays);forward={n:0 for n in model.order};pred={}
for u in model.order:
 for dest,eid in model.adj[u]:
  value=forward[u]+model.weights[eid]
  if value>forward[dest]:forward[dest]=value;pred[dest]=eid
end=max(model.terminals,key=lambda n:forward[n]);assert forward==model.forward;critical=[]
while end in pred:eid=pred[end];critical.append(eid);end=model.edges[eid]['source']
critical.reverse();assert sum(model.weights[eid] for eid in critical)==model.cpd
selected=sorted({allocation['edge_connection_ids'][eid] for eid in critical if eid in allocation['edge_connection_ids']});D=R/'experiments/fresh_critical_owner_discovery_v1_2026-10-08';D.mkdir(exist_ok=False)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,selected_connections=selected,critical_timing_edge_ids=critical,policy='Selection from attaining full fixed-local DAG path of freshly repaired state. All selected connections, FULL and RELAX_OTHER_OWNERS, original budgets and retained sameNET parents unchanged. Hypothetical only; no candidates committed. Model construction guard1000ns is computation range, not QoR target or changed budget. No historical critical/owner list read.'),indent=2)+'\n')
events=[]
from collections import Counter
for cid in selected:
 q=byid[cid];net=q['net_id'];kept,fixed=ledger.view(cid);outside=ledger.occupancy.copy();outside.subtract(ledger.nodes[net].keys());ceiling=limits[cid].numerator//limits[cid].denominator
 for scenario in ('FULL_CONSTRAINTS','RELAX_OTHER_OWNERS'):
  tick=time.perf_counter();answer=native.query(q['source'],q['sink'],ceiling,outside if scenario=='FULL_CONSTRAINTS' else Counter(),kept,fixed,len(f['edge_ids'])+1,1);blockers={}
  if answer['status']=='FOUND':
   if 'nextslot' not in globals():nextslot={eid:i for i,eid in enumerate(f['edge_ids'])}
   for eid in answer['physical_edge_ids']:
    node=f['dest_ranks'][nextslot[eid]]
    if outside[node]>=f['capacities'][node]:blockers[str(node)]=sorted(owner for owner,used in ledger.nodes.items() if owner!=net and node in used)
  events.append(dict(connection_id=cid,scenario=scenario,search=answer,search_seconds=time.perf_counter()-tick,blocking_nodes=blockers,blocking_net_ids=sorted({owner for owners in blockers.values() for owner in owners})))
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),scale=rc.scale,model_cpd_ns=str(model.cpd_seconds()*10**9),critical_timing_edge_ids=critical,selected_connections=selected,events=events,base_state_sha256=sha(br),component_elapsed_seconds=time.perf_counter()-started,scope='Fresh critical/owner discovery only, no transaction execution or native acceptance. Relaxed paths hypothetical; blocker set from one attaining path is not a minimal release set. Source raw-route import is redundantly charged in this standalone adapter.'),indent=2)+'\n');native.close();print('selected',selected,'owners',[(e['connection_id'],e['blocking_net_ids']) for e in events if e['scenario']=='RELAX_OTHER_OWNERS'],flush=True)
