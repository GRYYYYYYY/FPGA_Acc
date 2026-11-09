"""Recover null sparse-floor contract; independently XML-audit all sampled edges."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from collections import Counter
from shortest_NET_tree_ensemble_v1 import sample
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 parent=R/'experiments/mmc_shortest_NET_tree_ensemble_pilot_v1_2026-10-19';proto=parent/'protocol.json';spec=json.loads(proto.read_text());support=parent/'predecessor_support.json';j=json.loads(support.read_text());prepared=dict(source=j['source'],sinks=j['sinks'],choices={int(v):tuple(map(tuple,row)) for v,row in j['choices'].items()},distance={int(v):tuple(x) for v,x in j['distance'].items()});framefile=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19/episode_01/native_retained/initial.json';frame=json.loads(framefile.read_text());floor={x['sink']:x['floor_integer'] for x in frame['records'] if x['net_id']==spec['net_id']};assert all(type(x) is int for x in floor.values()) and set(floor)==set(prepared['sinks']);assert all(prepared['distance'][s][0]==floor[s] for s in floor)
 graph=next(pathlib.Path(p) for p in spec['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==spec['bindings'][str(graph)];rows=[];needed=set();nodes=set()
 for i in range(16):
  tree=sample(prepared,seed=19,net_id=spec['net_id'],sample_index=i);rows.append(dict(sample_index=i,nodes=sorted(tree['nodes']),paths={str(s):list(p) for s,p in tree['paths'].items()}));needed.update(tree['edge_ids']);nodes.update(tree['nodes']);assert len(tree['edge_ids'])==len(tree['nodes'])-1
 O=R/'experiments/mmc_shortest_NET_tree_ensemble_pilot_v2_2026-10-19';O.mkdir();files=[proto,support,framefile,graph,pathlib.Path(__file__).resolve(),R/'tools/shortest_NET_tree_ensemble_v1.py'];bindings={str(p):sha(p) for p in files};write(O/'protocol.json',dict(bindings=bindings,recovery='Null sparse fresh_raw floors replaced by fully numeric matched-V2 frame. No source support/search/NET/sample-count/seed change.',registered_old_minimum_dual_scope_still_false=True))
 selected_nodes={};switches={};selected_edges={};stack=[];eid=0
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parenttag=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parenttag=='rr_nodes' and int(e.get('id')) in nodes:
   t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0;selected_nodes[int(e.get('id'))]=(e.get('type'),int(e.get('capacity')))
  elif e.tag=='switch' and parenttag=='switches':
   t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0;switches[int(e.get('id'))]=Fraction(t.get('Tdel','0'))*10**18
  elif e.tag=='edge' and parenttag=='rr_edges':
   if eid in needed:selected_edges[eid]=(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id')))
   eid+=1
  if (e.tag,parenttag) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert eid==8097539 and set(selected_edges)==needed and set(selected_nodes)==nodes;occupancy=Counter();source=prepared['source']
 for row in rows:
  union={source};parents={}
  for sink,path in row['paths'].items():
   sink=int(sink);u=source;cost=Fraction(0);seen={u};assert selected_nodes[u][0]=='SOURCE'
   for i,edge in enumerate(path):
    a,v,sw=selected_edges[edge];assert a==u and v not in seen and selected_nodes[v][1]>0
    assert selected_nodes[v][0]=='SINK' if i==len(path)-1 else selected_nodes[v][0] not in ['SOURCE','SINK']
    assert v not in parents or parents[v]==(u,edge);parents[v]=(u,edge);seen.add(v);cost+=switches[sw];u=v
   assert u==sink and cost==floor[sink] and len(path)==prepared['distance'][sink][1];union.update(seen)
  assert union==set(row['nodes']);occupancy.update(union)
 write(O/'samples.json',rows);write(O/'occupancy_counts.json',dict(occupancy))
 for p in O.iterdir():
  if p.is_file():bindings[str(p)]=sha(p)
 write(O/'verification.json',dict(status='REAL_NET_16_TREE_SAMPLES_INDEPENDENT_XML_PATH_BUDGET_PARENT_AND_NET_OCCUPANCY_PASS',bindings=bindings,net_id=spec['net_id'],sinks=len(floor),sample_count=16,support_nodes=len(prepared['distance']),branching_support_nodes=sum(len(x)>1 for x in prepared['choices'].values()),distinct_node_unions=len({tuple(x['nodes']) for x in rows}),all_cached_old_minimum_duals_recertified=False,scope='Single input-selected NET only, recovered sparse-floor contract. XML arc/cost/capacity/terminal and shared-parent correctness proven. No full multiNET ensemble, congestion forecast quality, new global minimum dual certificate, STA or full-flow speed claim.'))
 print('REAL NET XML AUDIT PASS',len(floor),len(prepared['distance']),len({tuple(x['nodes']) for x in rows}),flush=True)
if __name__=='__main__':main()
