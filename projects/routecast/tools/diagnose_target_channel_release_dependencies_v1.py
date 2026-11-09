"""Diagnostic cold-target channel release graph; never proposes forecast candidates."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_target_NET_constraints_v1_2026-10-20';A=E/'prospective_external_family_capacity_retry_v1_2026-10-20';D=E/'prospective_external_family_target_release_dependencies_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scc(adj):
 seen=set();order=[];rev={n:set() for n in adj}
 for u,vs in adj.items():
  for v in vs:rev[v].add(u)
 for start in adj:
  if start in seen:continue
  seen.add(start);stack=[(start,False)]
  while stack:
   u,done=stack.pop()
   if done:order.append(u);continue
   stack.append((u,True))
   for v in sorted(adj[u],reverse=True):
    if v not in seen:seen.add(v);stack.append((v,False))
 assigned={};components=[]
 for start in reversed(order):
  if start in assigned:continue
  cid=len(components);members=[];queue=[start];assigned[start]=cid
  while queue:
   u=queue.pop();members.append(u)
   for v in rev[u]:
    if v not in assigned:assigned[v]=cid;queue.append(v)
  components.append(sorted(members))
 return components,assigned,rev

def main():
 proof=read(I/'independent_verification_v1.json');assert proof['status']=='ALL17757_NET_CONSTRAINT_CLASSIFICATIONS_INDEPENDENT_XML_AND_RATIONAL_SCORE_PASS';cases=read(A/'protocol.json')['cases'];frames={};needed=set()
 for c in cases:
  old=read(Path(c['warm'])/'native_retained/initial.json')['records'];new=read(I/c['case']/'target_records.json');frames[c['case']]=old,new
  for q in old+new:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);dest={};channels=set();eid=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes' and e.get('type') in ('CHANX','CHANY'):assert int(e.get('capacity'))==1;channels.add(int(e.get('id')))
  elif e.tag=='edge' and parent=='rr_edges':
   if eid in needed:dest[eid]=int(e.get('sink_node'))
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(dest)==needed;D.mkdir(exist_ok=False);bindings={str(I/'independent_verification_v1.json'):sha(I/'independent_verification_v1.json'),str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for c in cases:
  case=c['case'];old,new=frames[case];supports=[]
  for records in (old,new):
   ns=defaultdict(set)
   for q in records:ns[q['net_id']].update(dest[e] for e in q['answer']['physical_edge_ids'] if dest[e] in channels)
   supports.append(ns)
  before,after=supports;owners=defaultdict(set);targetowners=defaultdict(set)
  for n,ns in before.items():
   for u in ns:owners[u].add(n)
  for n,ns in after.items():
   for u in ns:targetowners[u].add(n)
  assert all(len(ns)<=1 for ns in targetowners.values());adj={n:set() for n in before};reasons=defaultdict(set)
  for n,ns in after.items():
   for u in ns-before[n]:
    for other in owners[u]-{n}:assert u not in after[other];adj[n].add(other);reasons[n,other].add(u)
  comps,assignment,rev=scc(adj);dag={i:set() for i in range(len(comps))};reverse={i:set() for i in dag}
  for n,deps in adj.items():
   for m in deps:
    a,b=assignment[n],assignment[m]
    if a!=b:dag[a].add(b);reverse[b].add(a)
  # Certificate: each component is internally strongly connected, quotient acyclic.
  for i,members in enumerate(comps):
   allowed=set(members)
   for graphadj in (adj,rev):
    reached={members[0]};todo=[members[0]]
    while todo:
     u=todo.pop()
     for v in graphadj[u]&allowed:
      if v not in reached:reached.add(v);todo.append(v)
    assert reached==allowed
  degree={i:len(v) for i,v in dag.items()};queue=deque(i for i,v in degree.items() if v==0);processed=[]
  while queue:
   u=queue.popleft();processed.append(u)
   for v in reverse[u]:
    degree[v]-=1
    if degree[v]==0:queue.append(v)
  assert len(processed)==len(comps)
  constraints={q['net_id']:q for q in read(I/case/'NET_constraints.json')};bad={n for n,q in constraints.items() if q['budget_violating_CIDs']};blocked={assignment[n] for n in bad};todo=list(blocked)
  while todo:
   u=todo.pop()
   for v in reverse[u]:
    if v not in blocked:blocked.add(v);todo.append(v)
  for cid in processed:assert (cid in blocked)==(any(n in bad for n in comps[cid]) or any(v in blocked for v in dag[cid]))
  cohort={n for n,q in constraints.items() if q['target_changing_clean'] and not q['budget_violating_CIDs']};payload=dict(adjacency={str(n):sorted(vs) for n,vs in adj.items()},components=comps,component_dependencies={str(i):sorted(vs) for i,vs in dag.items()},budget_blocked_components=sorted(blocked),pressure_release_reasons=[dict(requester=n,releaser=m,channels=sorted(ns)) for (n,m),ns in sorted(reasons.items())]);out=D/case;out.mkdir(parents=True);p=out/'dependencies.json';p.write_text(json.dumps(payload)+'\n');sizes=sorted(map(len,comps),reverse=True);row=dict(case=case,NETs=len(adj),dependency_arcs=sum(map(len,adj.values())),SCCs=len(comps),nontrivial_SCCs=sum(n>1 for n in sizes),largest_SCC_sizes=sizes[:10],budget_compatible_target_changing_clean_NETs=len(cohort),cohort_release_closure_touches_budget_incompatible_NET=sum(assignment[n] in blocked for n in cohort),cohort_in_nontrivial_SCC=sum(len(comps[assignment[n]])>1 for n in cohort),SCC_strong_connectivity_and_quotient_acyclicity_certified=True);results.append(row);print(json.dumps(row),flush=True)
  for p in [p,I/case/'target_records.json',I/case/'NET_constraints.json',Path(c['warm'])/'native_retained/initial.json']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_CHANNEL_RELEASE_GRAPH_SCC_AND_BUDGET_CLOSURE_CERTIFICATES_PASS',rows=results,bindings=bindings,scope='Exact target-path channel release dependencies for unit-capacity channels. Describes simultaneous resource exchange under per-node no-new-pressure interpretation; original total-overflow guard may permit compensating new pressure. Not necessary closure for every legal original-guard sequence, not a predictor and no aggregate impossibility proof.'),indent=2)+'\n')
if __name__=='__main__':main()
