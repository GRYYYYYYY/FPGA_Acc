"""All-round original XML edge/switch membership and rooted tree structure.
Does not certify delays, criticality timing, or manifest sink coverage.
"""
import json,xml.etree.ElementTree as E
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_iteration_state_observer_v1_2026-10-10'
v=json.loads((O/'verification.json').read_text());assert v['route_bytes_equal_fully_audited_cold']
assert all(sha(p)==h for p,h in v['bindings'].items())
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';e=json.loads(ep.read_text());graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256']
requested=set();rows=[]
for iteration in range(1,22):
 p=O/'states'/f'round_{iteration}.tsv';assert sha(p)==v['bindings'][str(p)]
 trees={};duplicates=0;records=0
 with p.open() as s:
  for line in s:
   f=line.split()
   if f[0]!='T':continue
   net,n,parent,switch=map(int,f[1:5]);records+=1;tree=trees.setdefault(net,{})
   if n in tree:
    assert tree[n]==(parent,switch),(iteration,net,n,'conflicting parent');duplicates+=1
   tree[n]=(parent,switch)
   if parent>=0:requested.add((parent,n,switch))
 for net,tree in trees.items():
  roots=[n for n,(p,sw) in tree.items() if p==-1];assert len(roots)==1
  done={roots[0]}
  for n in tree:
   trail=set();u=n
   while u not in done:
    assert u in tree and u not in trail,(iteration,net,n,'cycle or missing parent');trail.add(u);u=tree[u][0]
   done.update(trail)
 rows.append({'iteration':iteration,'nets':len(trees),'records':records,'duplicate_node_records':duplicates})
 print('TREE STRUCTURE',iteration,records,flush=True)
found=set();stack=[];switches=set()
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='switch':switches.add(int(el.get('id')));stack[-2].remove(el);el.clear()
 elif el.tag=='edge':
  key=(int(el.get('src_node')),int(el.get('sink_node')),int(el.get('switch_id')))
  if key in requested:found.add(key)
  stack[-2].remove(el);el.clear()
 elif el.tag=='node':stack[-2].remove(el);el.clear()
 stack.pop()
assert requested==found,('missing XML arcs',len(requested-found),list(requested-found)[:10]);assert all(s in switches for _,_,s in requested)
assert all(sha(p)==h for p,h in v['bindings'].items())
f=O/'tree_edge_audit_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':{**v['bindings'],str(O/'verification.json'):sha(O/'verification.json'),str(graph):sha(graph),str(ep):sha(ep),str(Path(__file__).resolve()):sha(Path(__file__))},'all21rounds_rooted_acyclic_parent_structure_and_original_XML_edge_switch_membership_pass':True,'distinct_arc_switch_triples':len(requested),'rows':rows,'scope':'Tree structure and original XML arc/switch membership only. Duplicate nodes require same parent/switch; sink/pin identity and delays not audited. No full physical/native equivalence or quality claim.'},indent=2)+'\n')
print('TREE XML AUDIT PASS',len(requested),flush=True)
