"""Full old-route import parity; sparse arc enumeration retains unique-arc checks."""
import json,time
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete as reference
from load_complete_route_state_v2 import load_complete as candidate
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/used_source_route_import_v2_2026-10-08';D.mkdir(exist_ok=False)
pp=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(pp.read_text())['cases'];rows=[];bindings={str(pp):sha(pp)}
for width in (8,16,32):
 c=next(c for c in cases if c['width']==width);ep=Path(c['old']);meta=json.loads(ep.read_text());g,h,nodes,f,rc,q=load_endpoints(ep);route=g.with_name('design.route')
 bindings.update({str(ep):sha(ep),str(route):sha(route),**{v['path']:v['sha256'] for v in meta['inputs'].values()}})
 start=time.perf_counter();a=reference(route,meta,nodes,f,rc);at=time.perf_counter()-start
 start=time.perf_counter();b=candidate(route,meta,nodes,f,rc);bt=time.perf_counter()-start
 assert a[0]==b[0] and a[1]==b[1] and vars(a[2])==vars(b[2])
 needed={(u,v,s) for path in b[0].values() for (u,_),(v,s) in zip(path,path[1:])};sources={u for u,v,s in needed}
 examined=sum(f['row_offsets'][u+1]-f['row_offsets'][u] for u in sources)
 # Reintroducing an existing required arc in a source row must still reject.
 u,v,s=next(iter(needed));slot=next(i for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['dest_ranks'][i]==v and f['switch_ids'][i]==s)
 other=next((i for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if i!=slot),None)
 if other is not None:
  old=(f['dest_ranks'][other],f['switch_ids'][other]);f['dest_ranks'][other]=v;f['switch_ids'][other]=s
  try:
   try:candidate(route,meta,nodes,f,rc)
   except ValueError as e:assert 'nonunique or absent' in str(e)
   else:raise AssertionError('Duplicate required arc accepted')
  finally:f['dest_ranks'][other],f['switch_ids'][other]=old
  assert candidate(route,meta,nodes,f,rc)[1]==a[1]
 else:raise AssertionError('No corruption fixture available')
 row=dict(width=width,connections=len(q),all_state_rows_ledger_equal=True,total_edges=len(f['edge_ids']),examined_edges=examined,source_nodes=len(sources),reference_seconds=at,candidate_seconds=bt,duplicate_required_arc_rejected_and_recovered=True);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
for name in ('load_complete_route_state_v1.py','load_complete_route_state_v2.py','verify_used_source_route_import_v2.py','class_cached_rc_endpoint_context_v1.py','incremental_shared_tree_ledger_v1.py','native_route_ledger_import_compact.py'):
 p=R/'tools'/name;bindings[str(p)]=sha(p)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Full three original mux routes: state, all exact integer delays/edge IDs and every shared ledger field parity. Controlled in-memory duplicate arc rejection/recovery. Same RC object reference then candidate (arc memo warmed), single sequential clocks cannot prove gain; no native rerun or budget admission.'),indent=2)+'\n')
