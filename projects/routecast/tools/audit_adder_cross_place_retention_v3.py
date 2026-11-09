"""Measure endpoint-only reuse against independently certified legal target witnesses."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_legal_route_budget_fixture_v1_2026-10-09';D=E/'adder_cross_place_retention_v3_2026-10-09';D.mkdir(exist_ok=False)
start=time.perf_counter();receipt=json.loads((B/'receipt.json').read_text());v=B/'verification.json';report=json.loads(v.read_text());bindings={**receipt['bindings'],**report['bindings'],str(v):sha(v),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items())
plans=receipt['plans'];metas=[json.loads(Path(p['endpoints']).read_text()) for p in plans];states=[{int(cid):tuple(tuple(x) for x in path) for cid,path in json.loads(Path(p['state']).read_text())['state'].items()} for p in plans]
g=Path(metas[0]['inputs']['graph']['path']);inv=read(g,metas[0]['graph_sha256'])
rows=[]
def inspect(state,queries,budgets):
 owners=defaultdict(set);parents=defaultdict(dict);conflict_nets=set();parent_conflicts=[];fail=[]
 for cid,path in state.items():
  q=queries[cid];net=q['net_id'];assert path[0]==(q['source'],None) and path[-1][0]==q['sink']
  assert len({n for n,_ in path})==len(path)
  r,c=inv.classes[inv.node_classes[q['source']]];delay=r*c/2
  for n,_ in path:owners[n].add(net)
  for (u,_),(v,sw) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,sw))==1
   old=parents[net].get(v)
   if old is not None and old!=(u,sw):conflict_nets.add(net);parent_conflicts.append([net,v])
   parents[net][v]=(u,sw)
   r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[sw];delay+=(sr+r/2)*c+td
  if delay>budgets[cid]:fail.append(cid);conflict_nets.add(net)
 overflow=[]
 for n,nets in owners.items():
  if len(nets)>int(inv.physical.nodes[n][1]):overflow.append(dict(node=n,owners=sorted(nets)));conflict_nets.update(nets)
 return dict(capacity_conflicts=overflow,parent_conflicts=parent_conflicts,budget_failure_ids=sorted(fail)),conflict_nets
for step in range(1,4):
 old,new=states[step-1],states[step];oq={q['connection_id']:q for q in metas[step-1]['connections']};q={x['connection_id']:x for x in metas[step]['connections']};assert set(oq)==set(q)==set(old)==set(new)
 assert all(oq[c]['net_id']==q[c]['net_id'] and metas[step-1]['net_names'][str(oq[c]['net_id'])]==metas[step]['net_names'][str(q[c]['net_id'])] for c in q)
 budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(Path(plans[step]['budgets']).read_text())}
 changed={c for c in q if (oq[c]['source'],oq[c]['sink'])!=(q[c]['source'],q[c]['sink'])};changed_paths={c for c in q if old[c]!=new[c]};nets={q[c]['net_id'] for c in changed};history=[]
 endpoint_hybrid={c:new[c] if c in changed else old[c] for c in q};endpoint_proof,_=inspect(endpoint_hybrid,q,budgets)
 while True:
  hybrid={c:new[c] if q[c]['net_id'] in nets else old[c] for c in q};proof,needs=inspect(hybrid,q,budgets);add=needs-nets
  history.append(dict(replaced_nets=sorted(nets),new_nets=sorted(add),**proof))
  if not add:
   assert not proof['capacity_conflicts'] and not proof['parent_conflicts'] and not proof['budget_failure_ids'];break
  nets.update(add)
  assert len(history)<=len({x['net_id'] for x in q.values()})+1
 replaced={c for c in q if q[c]['net_id'] in nets};retained=set(q)-replaced
 statefile=D/f'step_{step}_hybrid_state.json';statefile.write_text(json.dumps({str(c):p for c,p in hybrid.items()},indent=2)+'\n');bindings[str(statefile)]=sha(statefile)
 row=dict(step=step,endpoint_changed=len(changed),cold_witness_path_changed=len(changed_paths),endpoint_unchanged_but_cold_path_changed=len(changed_paths-changed),endpoint_only_hybrid=endpoint_proof,closure_iterations=history,replaced_connections=len(replaced),retained_connections=len(retained),replaced_nets=len(nets),retained_old_paths_exact=all(hybrid[c]==old[c] for c in retained),final_model_physical_parent_capacity_pass=True)
 rows.append(row);print(dict(step=step,endpoint_changed=len(changed),cold_witness_path_changed=len(changed_paths),replaced_connections=len(replaced),retained_connections=len(retained),iterations=len(history)),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Offline target-witness-dependent closure, independent original XML/Fraction validation. Not minimal required update set, online search, native certification of hybrid state, transaction rollback or speedup. Positive-control budgets only.'),indent=2)+'\n')
