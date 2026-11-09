"""Actual failure-state capacity-only shortest paths, own NET union charged once."""
import sys,json,time,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_failure_capacity_v1_2026-10-07';out.mkdir();begin=time.perf_counter();parent=R/'experiments/misex_net466_budget_path_owner_joint_v3_2026-10-07';vp=parent/'branch_verification_dedup.json';v=json.loads(vp.read_text());assert v['states_verified']==8 and not v['local_solution_present'];rp=parent/'receipt.json';assert sha(rp)==v['bindings'][str(rp)];pr=json.loads(rp.read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(vp):sha(vp),str(rp):sha(rp),str(ep):sha(ep),str(fp):sha(fp)};bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()})
for a in pr['attempts']:assert sha(a['state_file'])==v['bindings'][a['state_file']];bindings[a['state_file']]=sha(a['state_file'])
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='All8 actual failed states; charge each NET union once, subtract failed NET own-node charge when testing capacity. Compute ordinary SOURCE-SINK shortest RC path under actual other-NET occupancy and original query budget, relaxing only currentNET parent consistency. Exact capped distance certificates plus paths for budget-feasible cases. No local replacement or partial commit.'),indent=2)+'\n');_,_,nodes,f,rc,queries=load_endpoints(ep);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};slots={e:i for i,e in enumerate(f['edge_ids'])};rows=[]
for a in pr['attempts']:
 state=json.loads(Path(a['state_file']).read_text());q=state['failure']['query'];net=q['net_id'];owners=defaultdict(set);treeparents={}
 for rec in state['records']:
  u=rec['source'];owners[rec['net_id']].add(u)
  for eid in rec['answer']['physical_edge_ids']:
   slot=slots[eid];v=f['dest_ranks'][slot];owners[rec['net_id']].add(v)
   if rec['net_id']==net:treeparents[v]=(u,eid)
   u=v
 ledger=Counter(n for own in owners.values() for n in own);assert ledger==Counter({int(n):c for n,c in state['ledger'].items()});allowed=bytes(ledger[n]-int(n in owners[net])<f['capacities'][n] for n in range(len(nodes)));floor=floors[q['source'],q['sink']];budget=max(rc.scale//10**9,(3*floor+1)//2);cap=budget+1;d=[cap]*len(nodes);parents={};d[q['source']]=min(cap,rc.initial(q['source'])) if allowed[q['source']] else cap;queue=[(d[q['source']],q['source'])] if d[q['source']]<cap else []
 while queue:
  delay,u=heapq.heappop(queue)
  if d[u]!=delay:continue
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if not allowed[v]:continue
   cost=min(cap,delay+rc.increments[slot])
   if cost<d[v]:d[v]=cost;parents[v]=(u,slot);heapq.heappush(queue,(cost,v))
 folder=out/f"branch{a['index']}";folder.mkdir();(folder/'allowed.bin').write_bytes(allowed);file=folder/'distances.bin';file.write_bytes(struct.pack('<'+str(len(nodes))+'Q',*d));path=None;conflicts=[]
 if d[q['sink']]<=budget:
  path=[];u=q['sink'];seen={u}
  while u!=q['source']:
   p,slot=parents[u];eid=f['edge_ids'][slot];assert p not in seen;seen.add(p);path.append(eid)
   if u in treeparents and treeparents[u]!=(p,eid):conflicts.append(u)
   u=p
  path.reverse();assert rc.path(q['source'],q['sink'],path)==d[q['sink']]
 rows.append(dict(branch=a['index'],state_file=a['state_file'],query=q,budget=budget,cap=cap,minimum_capped_delay=d[q['sink']],capacity_only_budget_feasible=path is not None,physical_edge_ids=path,current_tree_parent_conflict_nodes=sorted(conflicts),certificate_file=str(file),allowed_file=str(folder/'allowed.bin')));print('FAILURE CAPACITY',a['index'],q['net_id'],q['connection_id'],d[q['sink']],budget,path is not None,conflicts,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.rglob('*') if p.is_file()}),indent=2)+'\n')
