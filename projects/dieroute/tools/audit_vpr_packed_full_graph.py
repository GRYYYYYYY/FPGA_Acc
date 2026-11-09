"""Compare every native RR node/edge against complete packed PR graph sidecars."""
from array import array
from collections import Counter
import argparse,hashlib,json,math,struct
from pathlib import Path
import xml.etree.ElementTree as ET
p=argparse.ArgumentParser(description=__doc__)
for n in ['graph','input_prefix','topology_prefix','output']:p.add_argument(n,type=Path)
a=p.parse_args();files={}
def raw(prefix,suffix):
 f=Path(str(prefix)+suffix);data=f.read_bytes();files[str(f.resolve())]=hashlib.sha256(data).hexdigest();return data
nodes=raw(a.input_prefix,'.nodes');edges=raw(a.input_prefix,'.edges');resources=raw(a.input_prefix,'.resources');owners=raw(a.topology_prefix,'.node_die');boxes=raw(a.topology_prefix,'.node_box')
assert len(nodes)%8==len(edges)%8==0
n=len(nodes)//8;count_edges=len(edges)//8;assert len(resources)==16*n and len(owners)==2*n and len(boxes)==8*n
nr=array('d');nc=array('d');lengths=array('H');switches={};outdegree=array('I',[0])*n;expected=[];current=None;edge_cursor=0;checked_nodes=0

def flush():
 global edge_cursor,expected
 if current is None:return
 begin,count,length=struct.unpack_from('<IHH',nodes,8*current);assert begin==edge_cursor and count==len(expected) and length==lengths[current]
 expected.sort()
 actual=[]
 for i in range(begin,begin+count):
  dst,base,delay=struct.unpack_from('<IHH',edges,8*i);assert base==64;actual.append((dst,delay))
 assert actual==expected,('adjacency/delay mismatch',current)
 edge_cursor+=count;expected=[]

for _,e in ET.iterparse(a.graph,events=['end']):
 if e.tag=='switch':
  sid=int(e.attrib['id']);assert sid not in switches and e.attrib['type'] in ['mux','buffer','tristate','pass_gate','short']
  t=e.find('timing');v={} if t is None else t.attrib
  vals=[float(v.get(k,'0')) for k in ['Tdel','R','Cinternal']];assert all(math.isfinite(x) and x>=0 for x in vals)
  assert vals[2]==0,'Nonzero Cinternal requires reviewed delay semantics'
  switches[sid]=(vals[0],vals[1],e.attrib['type'] not in ['pass_gate','short']);e.clear()
 elif e.tag=='node':
  i=int(e.attrib['id']);assert i==checked_nodes<n
  loc=e.find('loc');t=e.find('timing');assert loc is not None and t is not None
  r,c=float(t.attrib.get('R','0')),float(t.attrib.get('C','0'));assert all(math.isfinite(v) and v>=0 for v in [r,c]);nr.append(r);nc.append(c)
  length=max(int(loc.attrib['xhigh'])-int(loc.attrib['xlow']),int(loc.attrib['yhigh'])-int(loc.attrib['ylow']))+1 if e.attrib['type'] in ['CHANX','CHANY'] else 0
  assert 0<=length<=65535;lengths.append(length)
  capacity=int(e.attrib['capacity']);assert 1<=capacity<=65535
  res=struct.unpack_from('<HHHHII',resources,16*i);assert res==(0,capacity,256,0,0,0xffffffff)
  assert struct.unpack_from('<H',owners,2*i)[0]==int(loc.attrib['layer'])
  assert struct.unpack_from('<HHHH',boxes,8*i)==tuple(int(loc.attrib[k]) for k in ['xlow','ylow','xhigh','yhigh'])
  checked_nodes+=1;e.clear()
 elif e.tag=='edge':
  src,dst,sid=(int(e.attrib[k]) for k in ['src_node','sink_node','switch_id']);assert max(src,dst)<n and sid in switches
  if current!=src:
   if current is not None:assert src>current
   flush();current=src
  delay,r,buffered=switches[sid]
  ps=(delay+r*nc[dst]+0.5*nr[dst]*nc[dst] if buffered else delay+0.5*r*nc[dst])*1e12
  assert math.isfinite(ps) and 0<=ps<=65535,'Quantization must not clamp'
  expected.append((dst,round(ps)));outdegree[src]+=1;e.clear()
flush();assert checked_nodes==n and edge_cursor==count_edges
for i,count in enumerate(outdegree):
 begin,degree,length=struct.unpack_from('<IHH',nodes,8*i);assert degree==count and length==lengths[i]
files[str(a.graph.resolve())]=hashlib.sha256(a.graph.read_bytes()).hexdigest();files[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
r=dict(status='all_native_rr_nodes_edges_layers_capacities_and_local_delay_fields_match_packed_graph',nodes=n,edges=count_edges,switches=len(switches),zero_outdegree_nodes=sum(c==0 for c in outdegree),source_sha256=files,scope='Full dense node IDs retained including isolated records;every native directed edge compared with packed CSR destination/local RC ps quantization,constant temporarybase64,pernodecapacity/layer/box. Requires zeroCinternal;no silentclamp. Not complete VPR float/treeRC equivalence,nativeindexedcost calibration,algorithmQoRorphysical mapping.')
with a.output.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(dict(status=r['status'],nodes=n,edges=count_edges)))
