"""Conservative full capacity/shared-parent decomposition of residual step3 bank."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from finite_route_bank_solver_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'online_cost_replay_v5_adder_online_component_solve_v3_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'online_cost_replay_v5_adder_online_owner337_detours_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());meta=json.loads((E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json').read_text());q={x['connection_id']:x for x in meta['connections']};bank={int(c):p for c,p in json.loads((E/'online_cost_replay_v5_adder_online_owner337_detours_v1_2026-10-09/step_3.json').read_text())['bank'].items()};from finite_route_bank_arc_consistency_v1 import propagate
inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);cap={n:int(c) for n,(kind,c) in inv.physical.nodes.items()};prop=propagate(bank,q,cap);(D/'propagation.json').write_text(json.dumps(prop,indent=2)+'\n');bindings[str(D/'propagation.json')]=sha(D/'propagation.json');assert prop['status']=='ARC_CONSISTENT';domains={int(c):p for c,p in prop['domains'].items()};filtered={c:[bank[c][i] for i in domains[c]] for c in bank};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);cap={n:int(c) for n,(kind,c) in inv.physical.nodes.items()};node_users=defaultdict(set);parent_users=defaultdict(lambda:defaultdict(set));adj={c:set() for c in bank};couplings=[]
for cid,options in filtered.items():
 for option in options:
  path=option['path']
  for n,s in path:node_users[n].add(cid)
  for (u,_),(n,s) in zip(path,path[1:]):parent_users[q[cid]['net_id'],n][cid].add((u,s))
def connect(group,kind,key):
 group=sorted(group)
 if len(group)<2:return
 for cid in group[1:]:adj[group[0]].add(cid);adj[cid].add(group[0])
 couplings.append(dict(kind=kind,key=key,connections=group))
for n,users in node_users.items():
 if len({q[c]['net_id'] for c in users})>cap[n]:connect(users,'CAPACITY',n)
for key,users in parent_users.items():
 if len(set.union(*users.values()))>1:connect(users,'PARENT',list(key))
remaining=set(bank);components=[]
while remaining:
 frontier=[min(remaining)];component=set()
 while frontier:
  cid=frontier.pop()
  if cid in component:continue
  component.add(cid);frontier.extend(adj[cid]-component)
 remaining-=component;components.append(sorted(component))
(D/'decomposition.json').write_text(json.dumps(dict(domains=domains,components=components,couplings=couplings),indent=2)+'\n');bindings[str(D/'decomposition.json')]=sha(D/'decomposition.json');print(dict(components=len(components),size_histogram=dict(Counter(map(len,components)))),flush=True);results=[];selection={}
for index,cids in enumerate(components):
 result=solve({c:filtered[c] for c in cids},q,cap,max_nodes=100000);p=D/f'component_{index}.json';p.write_text(json.dumps(dict(connections=cids,result=result),indent=2)+'\n');bindings[str(p)]=sha(p);results.append(dict(component=index,connections=len(cids),status=result['status'],visited_nodes=result['visited_nodes']))
 if result['status']=='FOUND':selection.update({c:domains[c][i] for c,i in result['selection'].items()})
 if len(cids)>1 or result['status']!='FOUND':print(results[-1],flush=True)
status='FINITE_BANK_EXHAUSTED' if any(r['status']=='FINITE_BANK_EXHAUSTED' for r in results) else 'SEARCH_LIMIT' if any(r['status']=='SEARCH_LIMIT' for r in results) else 'FOUND'
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,results=results,status=status,selection=selection if status=='FOUND' else None,component_seconds=time.perf_counter()-start,scope='Conservative capacity including higher-order node groups and shared-parent decomposition. Component proofs and coupling completeness need independent replay; no global routing/native/timing/gain claim.'),indent=2)+'\n');print(status,flush=True)
