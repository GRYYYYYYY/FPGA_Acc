"""Independent actual occupancy, all-arc potentials and tight-path attainability audit."""
import sys,json,struct
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_failure_capacity_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());parent=R/'experiments/misex_net466_budget_path_owner_joint_v3_2026-10-07';prior=json.loads((parent/'receipt.json').read_text());pv=json.loads((parent/'branch_verification_dedup.json').read_text());assert len(r['rows'])==len(prior['attempts'])==pv['states_verified']==8;ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';_,_,nodes,f,rc,queries=load_endpoints(ep);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};checks=0;results=[]
for row,a in zip(r['rows'],prior['attempts']):
 assert row['branch']==a['index'] and row['state_file']==a['state_file'] and bindings[a['state_file']]==pv['bindings'][a['state_file']];state=json.loads(Path(a['state_file']).read_text());q=state['failure']['query'];assert row['query']==q==qm[q['connection_id']];net=q['net_id'];owners=defaultdict(set);tree={}
 for rec in state['records']:
  u=rec['source'];owners[rec['net_id']].add(u)
  for eid in rec['answer']['physical_edge_ids']:
   slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];v=f['dest_ranks'][slot];owners[rec['net_id']].add(v)
   if rec['net_id']==net:assert v not in tree or tree[v]==(u,eid);tree[v]=(u,eid)
   u=v
 ledger=Counter(n for own in owners.values() for n in own);assert ledger==Counter({int(n):c for n,c in state['ledger'].items()});assert all(c<=f['capacities'][n] for n,c in ledger.items());allowed=bytes(sum(n in own for owner,own in owners.items() if owner!=net)<f['capacities'][n] for n in range(len(nodes)));assert allowed==Path(row['allowed_file']).read_bytes();budget=max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2);cap=budget+1;assert row['budget']==budget and row['cap']==cap;raw=Path(row['certificate_file']).read_bytes();assert len(raw)==8*len(nodes);d=struct.unpack('<'+str(len(nodes))+'Q',raw);assert all(v<=cap for v in d);assert d[q['source']]==(min(rc.initial(q['source']),cap) if allowed[q['source']] else cap)
 for u in range(len(nodes)):
  if not allowed[u]:assert d[u]==cap;continue
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v]:assert d[v]<=min(cap,d[u]+rc.increments[edge]);checks+=1
 reached={q['source']} if allowed[q['source']] and d[q['source']]<cap else set();queue=deque(reached)
 while queue:
  u=queue.popleft()
  for edge in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][edge]
   if allowed[v] and v not in reached and d[v]<cap and d[v]==d[u]+rc.increments[edge]:reached.add(v);queue.append(v)
 assert reached=={n for n,x in enumerate(d) if x<cap};assert row['minimum_capped_delay']==d[q['sink']];feasible=d[q['sink']]<=budget;assert feasible==row['capacity_only_budget_feasible'];conflicts=[]
 if feasible:
  path=row['physical_edge_ids'];assert rc.path(q['source'],q['sink'],path)==d[q['sink']];u=q['source'];assert allowed[u]
  for eid in path:
   slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];v=f['dest_ranks'][slot];assert allowed[v]
   if v in tree and tree[v]!=(u,eid):conflicts.append(v)
   u=v
  assert u==q['sink']
 else:assert row['physical_edge_ids'] is None
 assert sorted(conflicts)==row['current_tree_parent_conflict_nodes'];results.append(dict(branch=row['branch'],capacity_only_budget_feasible=feasible,parent_conflicts=len(conflicts)));print('PASS failure capacity',row['branch'],feasible,len(conflicts),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=results,actual_failure_states_verified=8,exact_capped_distance_certificates=8,all_arc_inequalities=checks,scope='Other-NET actual occupancy charged once; currentNET tree relaxed. Overbudget certificate proves capacity/budget obstruction under actual others. A feasible path with parent conflicts is a tree-rebuild diagnostic, never accepted replacement/native QoR or workflow gain.'),indent=2)+'\n');print('PASS exact failure classification',checks,flush=True)
