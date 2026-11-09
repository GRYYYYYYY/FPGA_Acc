"""Original integer-delay RR XML arrays for graph-certificate generation."""
import xml.etree.ElementTree as ET
from array import array
from fractions import Fraction

def load_graph(path):
 caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[]
 for event,e in ET.iterparse(path,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert all(Fraction(t.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1 and w>=0;weights[int(e.get('id'))]=w.numerator
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));switches.append(int(e.get('switch_id')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert all(u<len(caps) and v<len(caps) and s in weights for u,v,s in zip(us,vs,switches))
 def csr(keys):
  offsets=array('I',[0])*(len(caps)+1)
  for node in keys:offsets[node+1]+=1
  for n in range(len(caps)):offsets[n+1]+=offsets[n]
  cursor=array('I',offsets);order=array('I',[0])*len(us)
  for eid,node in enumerate(keys):order[cursor[node]]=eid;cursor[node]+=1
  return offsets,order
 offsets,order=csr(us);reverse_offsets,reverse_order=csr(vs)
 return dict(caps=caps,types=types,us=us,vs=vs,switches=switches,weights=weights,offsets=offsets,order=order,reverse_offsets=reverse_offsets,reverse_order=reverse_order)

def candidate_nodes(candidate,dest):
 nodes={r['source'] for r in candidate['records']}
 for r in candidate['records']:nodes.update(dest[e] for e in r['answer']['physical_edge_ids'])
 return nodes
