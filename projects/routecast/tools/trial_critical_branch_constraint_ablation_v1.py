"""Sequential exact budgeted branch repair with immutable outside owners and retained parents."""
import json,heapq,sys
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
P=R/'experiments/branch_budget_single_replacement_v1_2026-10-08/diagnosis.json';prior=json.loads(P.read_text());assert all(sha(f)==h for f,h in prior['bindings'].items())
bindings={**prior['bindings'],**closure([Path(__file__)]),str(P):sha(P)}
protocol=json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text());case=next(c for c in protocol['cases'] if c['width']==32 and c['index']==2)
ep=Path(case['target']);meta=json.loads(ep.read_text());graph,digest,nodes,f,rc,queries=load_endpoints(ep);assert all(x>=0 for x in rc.increments)
route=R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route';observed={}
for name,branches in physical_paths(route).items():
 for path in branches:
  key=(name,path[0][0],path[-1][0]);assert key not in observed;observed[key]=path
state={q['connection_id']:observed[meta['net_names'][str(q['net_id'])],q['source'],q['sink']] for q in queries};byid={q['connection_id']:q for q in queries}
budget=json.loads(Path(case['budget']).read_text());srcslot=[u for u in range(len(nodes)) for _ in range(f['row_offsets'][u],f['row_offsets'][u+1])]
previous=R/'experiments/budget_occupied_branch_repair_v1_2026-10-08';proof=previous/'complete_frame_verification_v2.json';verified=json.loads(proof.read_text());assert all(sha(f)==h for f,h in verified['bindings'].items())
bindings.update(verified['bindings']);bindings[str(proof)]=sha(proof)
old_receipt=json.loads((previous/'receipt.json').read_text());state={int(cid):tuple(tuple(x) for x in path) for cid,path in old_receipt['state'].items()}
critical=R/'experiments/budget_model_native_sta_parity_v1_2026-10-08/critical_path_repair_overlap.json';critical_proof=json.loads(critical.read_text());bindings[str(critical)]=sha(critical)
selected=next(x['model_critical_path_connections'] for x in critical_proof['rows'] if x['mode']=='budget_repaired');assert selected==[832,1781,1892]
prior['rows']=[dict(connection_id=cid,status='REQUIRES_JOINT_REPAIR') for cid in selected]
D=R/'experiments/critical_branch_constraint_ablation_v1_2026-10-08';D.mkdir(exist_ok=False);events=[]
(D/'selection_protocol.json').write_text(json.dumps(dict(selected_connections=selected,critical_path_source_sha256=sha(critical),base_full_frame_sha256=sha(proof),policy='All three external connections on the authenticated base model attaining critical path, fixed order, before search; complete previous frame and original budgets preserved.'),indent=2)+'\n')

def rebuild():
 unions=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  net=byid[cid]['net_id'];unions[net].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
 ledger=Counter(n for union in unions.values() for n in union)
 assert all(count<=f['capacities'][n] for n,count in ledger.items())
 return unions,ledger
for item in [dict(x,scenario=scenario) for x in prior['rows'] for scenario in ('FULL_CONSTRAINTS','RELAX_OTHER_OWNERS','RELAX_RETAINED_PARENTS','RELAX_BOTH')]:
 cid=item['connection_id']
 if item['status'] not in ('SINGLE_REPLACEMENT_TREE_CAPACITY_SAFE','REQUIRES_JOINT_REPAIR'):continue
 q=byid[cid];net=q['net_id'];source,sink=q['source'],q['sink'];unions,ledger=rebuild();outside=ledger.copy();outside.subtract(unions[net]);parents={}
 for other,path in state.items():
  if other==cid or byid[other]['net_id']!=net:continue
  for (u,_),(v,s) in zip(path,path[1:]):
   assert v not in parents or parents[v]==(u,s);parents[v]=(u,s)
 scenario=item['scenario']
 if scenario in ('RELAX_OTHER_OWNERS','RELAX_BOTH'):outside=Counter()
 if scenario in ('RELAX_RETAINED_PARENTS','RELAX_BOTH'):parents={}
 limit=Fraction(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9*rc.scale;ceiling=limit.numerator//limit.denominator
 def allowed(u,slot):
  v=f['dest_ranks'][slot]
  return outside[v]<f['capacities'][v] and (v not in parents or parents[v]==(u,f['switch_ids'][slot]))
 assert outside[source]<f['capacities'][source]
 dist={source:rc.initial(source)};pred={};queue=[(dist[source],source)];settled=set();found=False
 while queue:
  value,u=heapq.heappop(queue)
  if value>ceiling:break
  if u in settled or value!=dist[u]:continue
  settled.add(u)
  if u==sink:found=True;break
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   if not allowed(u,slot):continue
   v=f['dest_ranks'][slot];candidate=value+rc.increments[slot]
   if candidate<=ceiling and candidate<dist.get(v,candidate+1):dist[v]=candidate;pred[v]=slot;heapq.heappush(queue,(candidate,v))
 clip=dist[sink] if found else ceiling+1
 # Independently check clipped potential inequalities on the constrained graph.
 pot={n:d for n,d in dist.items() if d<clip};assert pot.get(source,clip)==min(rc.initial(source),clip)
 checks=0
 for u,value in pot.items():
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   if allowed(u,slot):assert pot.get(f['dest_ranks'][slot],clip)<=value+rc.increments[slot];checks+=1
 certificate=dict(connection_id=cid,clip=clip,potentials={str(n):d for n,d in pot.items()},outside_occupancy={str(n):c for n,c in outside.items() if c},retained_parents={str(n):list(p) for n,p in parents.items()})
 cp=D/f'certificate_{cid}_{scenario}.json';cp.write_text(json.dumps(certificate,separators=(',',':'))+'\n');bindings[str(cp)]=sha(cp)
 event=dict(connection_id=cid,scenario=scenario,query=q,budget_integer_ceiling=ceiling,status='FOUND_CONSTRAINED_MINIMUM' if found else 'RETAIN_NO_CONSTRAINED_BUDGET_PATH',certificate=str(cp),certificate_sha256=sha(cp),edge_inequalities=checks,old_path=[list(x) for x in state[cid]])
 if found:
  slots=[];u=sink
  while u!=source:slot=pred[u];slots.append(slot);u=srcslot[slot]
  slots.reverse();path=[(source,None)]+[(f['dest_ranks'][slot],f['switch_ids'][slot]) for slot in slots];edges=[f['edge_ids'][slot] for slot in slots]
  assert len(set(n for n,s in path))==len(path) and rc.path(source,sink,edges)==dist[sink]<=ceiling
  event.update(new_path=[list(x) for x in path],physical_edge_ids=edges,delay_integer=dist[sink])
 events.append(event);print(cid,scenario,event['status'],flush=True)
unions,ledger=rebuild();assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,scale=rc.scale,events=events,complete_connections=len(state),state={str(cid):[list(x) for x in path] for cid,path in state.items()},scope='Sequential constrained branch proposals in exact buffered RC model, all queries preserved; two original budget-infeasible queries remain; critical-path research selection. No native serialization/packed pin/STA or end-to-end gain. Independent per-query four constraint scenarios; no proposals committed, no owner release performed. Hypothetical relaxed candidates are not joint legal routes. Producer potential checks require independent replay.'),indent=2)+'\n')
