"""Full current-bank negative-choice release witnesses, without target labels."""
import json,hashlib,xml.etree.ElementTree as ET
from array import array
from collections import defaultdict,deque
from pathlib import Path
from binary_capacity_dependency_v1 import components
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'prospective_external_family_blocker_release_v1_2026-10-19';C=E/'prospective_external_family_blocker_release_cnf_v1_2026-10-19';A=E/'prospective_external_family_propagated_mandatory_audit_v1_2026-10-19';O=E/'prospective_external_family_global_release_inventory_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def check_components(graph,groups):
 # Independent strong-connectivity checks plus acyclic quotient prove exactness.
 labels={n:i for i,g in enumerate(groups) for n in g};assert set(labels)==set(range(len(graph)))
 rev=[[] for _ in graph]
 for u,vs in enumerate(graph):
  for v in vs:rev[v].append(u)
 for i,g in enumerate(groups):
  for adjacency in (graph,rev):
   seen={g[0]};todo=[g[0]]
   while todo:
    for v in adjacency[todo.pop()]:
     if labels[v]==i and v not in seen:seen.add(v);todo.append(v)
   assert seen==set(g)
 quotient=[set() for _ in groups];indegree=[0]*len(groups)
 for u,vs in enumerate(graph):
  for v in vs:
   a,b=labels[u],labels[v]
   if a!=b and b not in quotient[a]:quotient[a].add(b);indegree[b]+=1
 todo=deque(i for i,d in enumerate(indegree) if not d);count=0
 while todo:
  u=todo.popleft();count+=1
  for v in quotient[u]:
   indegree[v]-=1
   if indegree[v]==0:todo.append(v)
 assert count==len(groups)
def main():
 proof=C/'independent_structure_verification_v1.json';p=read(proof);audit=A/'verification.json';ap=read(audit)
 for receipt in (p,ap):assert all(sha(q)==h for q,h in receipt['bindings'].items())
 graph=next(Path(q) for q in p['bindings'] if q.endswith('/rr_graph.xml'));caps=array('I');dest=array('I');types=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'))
  elif e.tag=='edge' and parent=='rr_edges':dest.append(int(e.get('sink_node')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 O.mkdir(exist_ok=False);rows=[];bindings={str(q):sha(q) for q in (proof,audit,graph,Path(__file__).resolve(),R/'tools/binary_capacity_dependency_v1.py')}
 for ep in range(1,4):
  case=f'w160/episode_{ep:02d}';cp=C/case/'encoding.json';bp=B/case/'candidate_bank.jsonl';dp=A/f'episode_{ep:02d}.json';cnf=read(cp);negative={-x[0] for x in cnf['clauses'] if len(x)==1 and x[0]<0};required=defaultdict(set);owned={}
  for line in bp.read_text().splitlines():
   data=json.loads(line);net=data['net_id'];options=[]
   for candidate in data['candidates']:
    nodes={r['source'] for r in candidate['records']}
    for r in candidate['records']:nodes.update(dest[eid] for eid in r['answer']['physical_edge_ids'])
    options.append(nodes)
   owned[net]=options
   for node in set.intersection(*options):
    if caps[node]==1:required[node].add(net)
  nets=sorted(owned);index={net:i for i,net in enumerate(nets)};graphNET=[set() for _ in nets];options=[];blocker_masks=defaultdict(set);blocker_options=defaultdict(set);blocker_requesters=defaultdict(set);conflicted={n for c in read(dp)['propagated_conflicts'] for n in c['NETs']};relevant_options=defaultdict(set)
  for variable,role in enumerate(cnf['variables'],1):
   if role['kind']!='CHOICE':continue
   net,option=role['key'];witnesses=[]
   for node in sorted(owned[net][option]):
    for blocker in sorted(required[node]-{net}):witnesses.append(dict(node=node,blocker_NET=blocker))
   assert bool(witnesses)==(variable in negative),(case,variable)
   if not witnesses:continue
   options.append(dict(variable=variable,net_id=net,option=option,witnesses=witnesses))
   for witness in witnesses:
    blocker=witness['blocker_NET'];node=witness['node'];graphNET[index[net]].add(index[blocker]);blocker_masks[blocker].add(node);blocker_options[blocker].add(variable);blocker_requesters[blocker].add(net)
    if net in conflicted:relevant_options[blocker].add(variable)
  _,groups,_=components([sorted(vs) for vs in graphNET]);check_components(graphNET,groups)
  release=[dict(net_id=net,resource_mask=sorted(mask),blocked_options=len(blocker_options[net]),requester_NETs=sorted(blocker_requesters[net]),options_in_propagated_conflict_NETs=len(relevant_options[net])) for net,mask in sorted(blocker_masks.items())]
  ranked=sorted(release,key=lambda r:(-r['options_in_propagated_conflict_NETs'],-r['blocked_options'],r['net_id']))
  result=dict(case=case,negative_options=options,blocker_groups=release,dependency_SCCs_NETs=[sorted(nets[i] for i in g) for g in groups],edge_semantics='Requester NET -> initial mandatory blocker NET for a specific currently excluded CHOICE. An option requires release of ALL its listed witnesses to become initially admissible without changing its path. A witness edge alone is not a forced selection or infeasibility proof; adding alternatives can invalidate current mandatory ownership.',group_masks_scope='Diagnostic union masks, not a generation policy: avoiding every witnessed resource at once may be stronger than needed or impossible. No ranking-based search or selected top-k action is authorized by this inventory.')
  out=O/f'episode_{ep:02d}.json';out.write_text(json.dumps(result,indent=2)+'\n')
  row=dict(case=case,negative_CHOICES=len(options),release_witnesses=sum(len(o['witnesses']) for o in options),dependency_edges=sum(map(len,graphNET)),blocker_NETs=len(release),blockers_affecting_propagated_conflict_NETs=sum(bool(r['options_in_propagated_conflict_NETs']) for r in release),largest_SCC_sizes=sorted((len(g) for g in groups),reverse=True)[:8],max_group_mask=max(map(len,blocker_masks.values()),default=0),top5_influence=[{k:r[k] for k in ('net_id','blocked_options','options_in_propagated_conflict_NETs')} for r in ranked[:5]],SCCs_independently_verified=True);rows.append(row)
  for q in (cp,bp,dp,out):bindings[str(q)]=sha(q)
  print('GLOBAL_RELEASE_INVENTORY',json.dumps(row),flush=True)
 assert all(sha(q)==h for q,h in bindings.items())
 (O/'verification.json').write_text(json.dumps(dict(status='ALL3_FULL_INITIAL_NEGATIVE_CHOICE_RELEASE_WITNESSES_AND_SCCS_VERIFIED',bindings=bindings,rows=rows,unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,promoted=False,scope='Snapshot dependency opportunity inventory only. All negative CHOICE units and exact resource witnesses covered. No candidate generation, global routing infeasibility, predictor, quality, utility or full runtime claim.'),indent=2)+'\n')
if __name__=='__main__':main()
