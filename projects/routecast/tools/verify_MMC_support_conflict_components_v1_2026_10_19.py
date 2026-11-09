"""Independent XML capacity and vertex-deletion witness audit; no dominators."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from collections import defaultdict,deque
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_support_conflict_components_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 rp=O/'results.json';summary=json.loads(rp.read_text())
 for p,h in summary['bindings'].items():assert sha(pathlib.Path(p))==h
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';admission=json.loads((M/'independent_prediction_verification_v1.json').read_text());journal=M/'NET_contributions.jsonl';assert admission['bindings'][str(journal)]==sha(journal)
 spec=json.loads((M/'protocol.json').read_text());graph=next(pathlib.Path(p) for p in spec['bindings'] if p.endswith('rr_graph.xml'));assert spec['bindings'][str(graph)]==sha(graph)
 cases=[json.loads((O/f'episode_0{i}.json').read_text()) for i in [1,2,3]];requirements=defaultdict(list);case_indices={};selectednodes=set()
 for case in cases:
  name=case['case'];idx=json.loads((M/name/'NET_contribution_indices.json').read_text());assert len(idx)==len(set(idx))==55300;case_indices[name]=set(idx);used=set();lower=0
  for block in case['disjoint_conflict_blocks']:
   assert block['capacity']==1 and len(block['members'])>=2;selectednodes.add(block['node']);members=set()
   for member in block['members']:
    n=member['net_id'];assert n not in used and n not in members;assert member['contribution_index'] in case_indices[name];members.add(n);requirements[member['contribution_index']].append((n,block['node'],member['dominated_sink']))
   used.update(members);assert block['required_support_departures']==len(members)-1;lower+=len(members)-1
  assert lower==case['certified_required_support_departures_lower_bound'] and len(used)==case['disjoint_block_NETs']
 caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   n=int(e.get('id'))
   if n in selectednodes:assert e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))==1;caps[n]=1
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert set(caps)==selectednodes;checked=set();seenindices=set()
 for line in journal.open():
  row=json.loads(line);i=row['index']
  if i not in requirements:continue
  seenindices.add(i);children=defaultdict(list)
  for node,parents in row['support_choices'].items():
   for parent,_ in parents:children[parent].append(int(node))
  def visit(blocked):
   found={row['source']};todo=deque(found)
   while todo:
    for node in children[todo.popleft()]:
     if node!=blocked and node not in found:found.add(node);todo.append(node)
   return found
  original=visit(-1)
  for net,node,sink in set(requirements[i]):
   assert row['net_id']==net and sink in row['sinks'] and sink in original and node!=row['source'];assert sink not in visit(node);checked.add((i,node,sink))
 assert seenindices==set(requirements)
 # Reconstruct connected components with union-find, independently of BFS producer.
 mandatory={}
 for line in (R/'experiments/mmc_NET_support_capacity_v1_2026-10-19/mandatory_contributions.jsonl').open():
  row=json.loads(line);mandatory[row['index']]=row
 for case in cases:
  parent={};edges=set();owners=defaultdict(list)
  def root(v):
   parent.setdefault(v,v)
   while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
   return v
  for i in case_indices[case['case']]:
   row=mandatory[i]
   for n in row['mandatory_channel_sink_witness']:owners[n].append(row['net_id'])
  for group in owners.values():
   if len(group)<2:continue
   for a in group:root(a)
   for a in group:parent[root(a)]=root(group[0])
   for j,a in enumerate(group):
    for b in group[j+1:]:edges.add(tuple(sorted((a,b))))
  groups=defaultdict(list)
  for a in parent:groups[root(a)].append(a)
  assert sorted(sorted(g) for g in groups.values())==sorted(case['components']);assert len(edges)==case['conflict_edges']
 bindings={str(p):sha(p) for p in [rp,journal,graph,pathlib.Path(__file__).resolve()]+[O/f'episode_0{i}.json' for i in [1,2,3]]}
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_DISJOINT_SUPPORT_DEPARTURE_BOUNDS_XML_AND_DELETION_CERTIFIED',unique_NET_supports_checked=len(seenindices),unique_vertex_deletion_witnesses=len(checked),distinct_capacity1_channels=len(caps),bindings=bindings,scope='Bounds certify departures from admitted supplied supports. Components independently union-find reconstructed from mandatory journal. No full-graph RC penalty or routed feasibility conclusion.'),f,indent=2)
 print('PASS',len(seenindices),'NET supports',len(checked),'deletion witnesses',flush=True)
if __name__=='__main__':main()
