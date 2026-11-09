"""All12 same-budget retention parity versus a fresh complete import per update."""
import json,time,sys,tempfile
from pathlib import Path
from fractions import Fraction as F
from retained_route_session_v1 import RetainedRouteSession
from class_cached_rc_endpoint_context_v1 import load_endpoints
from class_cached_rc_endpoint_session_v2 import clear_cache
from load_complete_route_state_v1 import load_complete
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/retained_route_session_v1_2026-10-08';D.mkdir(exist_ok=False)
sys.path.insert(0,str(R/'tools/native_resume_prototype'));from source_binding_v2 import closure
pp=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';protocol=json.loads(pp.read_text());bindings={**closure([Path(__file__)]),str(pp):sha(pp)};rows=[];clear_cache()
for width in (8,16,32):
 cases=sorted([c for c in protocol['cases'] if c['width']==width],key=lambda c:c['index'])
 first=cases[0];old=json.loads(Path(first['old']).read_text());route=Path(old['inputs']['graph']['path']).with_name('design.route')
 tick=time.perf_counter();session=RetainedRouteSession(first['old'],route);setup=time.perf_counter()-tick
 for c in cases:
  assert sha(c['old'])==sha(first['old'])
  tick=time.perf_counter();result=session.select(c['target'],c['budget']);selected=time.perf_counter()-tick
  tick=time.perf_counter();_,_,nodes,f,rc,queries=load_endpoints(c['old']);_,physical,_=load_complete(route,old,nodes,f,rc)
  byid={q['connection_id']:q for q in queries};delays={r['connection_id']:r for r in physical};target=json.loads(Path(c['target']).read_text());budget=json.loads(Path(c['budget']).read_text());keep=[];release=[]
  for q in sorted(target['connections'],key=lambda q:q['connection_id']):
   cid=q['connection_id'];before=byid[cid]
   if (q['source'],q['sink'])!=(before['source'],before['sink']):release.append(dict(connection_id=cid,reason='ENDPOINT_CHANGED'));continue
   delay=F(delays[cid]['delay_integer'],rc.scale);limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))
   if delay*10**9>limit:release.append(dict(connection_id=cid,reason='TARGET_BUDGET_UNSAFE',delay_seconds=str(delay),budget_ns=str(limit)));continue
   keep.append(dict(q,physical_edge_ids=delays[cid]['physical_edge_ids'],delay_seconds=str(delay),budget_ns=str(limit)))
  fresh=time.perf_counter()-tick
  assert result['retained']==keep and result['released']==release
  bindings.update(result['bindings']);rows.append(dict(width=width,index=c['index'],setup_seconds=setup if c['index']==0 else 0,selection_seconds=selected,fresh_reference_seconds=fresh,retained=len(keep),released=len(release)))
  if width==32 and c['index']==2:
   forest=R/'experiments/fresh_retained_branch_seed_v9_2026-10-08/forest.json';expected=json.loads(forest.read_text());assert result['retained']==expected['retained'] and result['released']==expected['released'];bindings[str(forest)]=sha(forest)
  if c['index']==0:result['retained'][0]['physical_edge_ids'].clear()
  print(width,c['index'],'retention parity',len(keep),len(release),flush=True)
 assert session.imports==1 and session.selections==4
# An invalid target is rejected without advancing the old epoch or selection count.
with tempfile.TemporaryDirectory(prefix='routecast-route-session-') as tmp:
 value=json.loads(Path(c['target']).read_text());value['connections']=value['connections'][:-1];bad=Path(tmp)/'bad.json';bad.write_text(json.dumps(value));before=session.selections
 try:session.select(bad,c['budget'])
 except ValueError:pass
 else:raise AssertionError('Incomplete target admitted')
 assert session.selections==before
 valid=session.select(c['target'],c['budget']);assert len(valid['retained'])+len(valid['released'])==len(value['connections'])+1
assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,complete12_retention_parity=True,isolated_returned_paths=True,invalid_target_atomic_rejection=True,scope='One complete old route import per graph, each update reauthenticates and evaluates full endpoint/budget retention. Fresh reference shares RC/physical import helpers; w32m2 additionally matches independently certified serialized forest. No new native seed/resume or all-budget feasibility/heldout/full-workflow gain proof.'),indent=2)+'\n')
print('PASS12 full retention decisions, returned-path isolation and invalid-target atomicity')
