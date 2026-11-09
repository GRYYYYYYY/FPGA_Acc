"""Fresh XML audit of every support edge and every sampled tree in fixed16NET batch."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_NET_tree_csr_batch_v1_2026-10-19';rp=O/'receipt.json';v=json.loads(rp.read_text());assert v['status']=='FIXED16_NET_SHARED_CSR_AND_256_SAMPLED_TREES_PATH_CHECK_PASS'
 for p,h in v['bindings'].items():assert sha(p)==h,p
 graph=next(pathlib.Path(p) for p in v['bindings'] if p.endswith('rr_graph.xml'));nets={row['net_id']:json.loads((O/f"net_{row['net_id']}.json").read_text()) for row in v['rows']};needed={eid for net in nets.values() for row in net['choices'].values() for _,eid in row};nodes={int(n) for net in nets.values() for n in net['distance']};edges={};nodeinfo={};switches={};stack=[];eid=0
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes' and int(e.get('id')) in nodes:
   t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0;nodeinfo[int(e.get('id'))]=(e.get('type'),int(e.get('capacity')))
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0;switches[int(e.get('id'))]=Fraction(t.get('Tdel','0'))*10**18
  elif e.tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=tuple(int(e.get(k)) for k in ['src_node','sink_node','switch_id'])
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(edges)==needed and set(nodeinfo)==nodes;checked=0
 for net in nets.values():
  source=net['source'];assert nodeinfo[source][0]=='SOURCE';distance={int(n):tuple(x) for n,x in net['distance'].items()};assert distance[source]==(0,0)
  for key,row in net['choices'].items():
   target=int(key)
   for u,e in row:
    a,b,sw=edges[e];assert (a,b)==(u,target);assert distance[target]==(distance[u][0]+switches[sw],distance[u][1]+1);assert nodeinfo[u][1]>0 and nodeinfo[target][1]>0
  assert len(net['samples'])==16
  for tree in net['samples']:
   union={source};parentmap={}
   for sink,path in tree['paths'].items():
    sink=int(sink);u=source;cost=Fraction(0);seen={source}
    for index,e in enumerate(path):
     a,b,sw=edges[e];assert a==u and b not in seen;assert nodeinfo[b][0]=='SINK' if index==len(path)-1 else nodeinfo[b][0] not in ['SOURCE','SINK'];assert b not in parentmap or parentmap[b]==(u,e);parentmap[b]=(u,e);seen.add(b);cost+=switches[sw];u=b
    assert u==sink and (cost,len(path))==distance[sink];union.update(seen)
   assert set(map(int,tree['paths']))==set(net['sinks']) and union==set(tree['nodes']);checked+=1
 assert checked==256
 p=O/'independent_XML_verification_v1.json';proof=dict(status='ALL16_NET_SUPPORT_EDGES_AND_256_TREES_INDEPENDENT_XML_PASS',bindings={str(rp):sha(rp),str(graph):sha(graph),str(pathlib.Path(__file__).resolve()):sha(__file__)},NETs=16,sampled_trees=checked,physical_support_edges=len(edges),support_nodes=len(nodes),global_shortest_dual_pending=True,scope='Original XML arc/RC/terminal/capacity and uniqueNET tree support verified. No global-minimum dual, full-design forecast quality, complete-time/hardware gain. Component times not representative workload extrapolation.')
 with p.open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(proof['status'],checked,len(edges),flush=True)
if __name__=='__main__':main()
