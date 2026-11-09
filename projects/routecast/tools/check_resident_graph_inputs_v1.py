"""Real byte mutation/path identity and immutable payload guard tests."""
import json,os,tempfile,xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace as N
from resident_graph_inputs_v1 import ResidentGraphInputs
from pre_route_endpoints import sha

def main():
 with tempfile.TemporaryDirectory() as directory:
  root=Path(directory);g=root/'a.xml';g.write_text('<g/>');other=root/'other';other.write_text('x');ep=root/'endpoint.json'
  def write(graph):ep.write_text(json.dumps(dict(inputs=dict(graph=dict(path=str(graph),sha256=sha(graph)),other=dict(path=str(other),sha256=sha(other))),graph_sha256=sha(graph),connections=[dict(connection_id=1)])))
  def load(p):
   x=json.loads(Path(p).read_text());graph=Path(x['inputs']['graph']['path']);node=ET.fromstring('<node id="0"><loc xlow="0"/></node>');rc=N(scale=1,increments=[2],initial=lambda i:3,path=lambda s,t,e:5)
   return graph,sha(graph),[node],dict(capacities=[1],edge_ids=[0]),rc,x['connections']
  write(g);cache=ResidentGraphInputs(load);a=cache(ep);a[-1][0]['connection_id']=999;b=cache(ep);assert b[-1][0]['connection_id']==1 and cache.stats['hits']==1;checks=1
  for change in [lambda:a[3].__setitem__('capacities',(2,)),lambda:a[2][0].attrib.__setitem__('id','1'),lambda:setattr(a[4],'scale',2)]:
   try:change()
   except (TypeError,AttributeError):checks+=1
   else:raise AssertionError('mutable snapshot')
  copy=root/'b.xml';copy.write_bytes(g.read_bytes());write(copy);cache(ep);assert cache.stats['misses']==2;checks+=1
  write(g);st=g.stat();g.write_text('<h/>');os.utime(g,ns=(st.st_atime_ns,st.st_mtime_ns))
  try:cache(ep)
  except ValueError:checks+=1
  else:raise AssertionError('stale graph accepted')
  write(g);other.write_text('y')
  try:cache(ep)
  except ValueError:checks+=1
  else:raise AssertionError('mutated endpoint input')
 print('ALL7_RESIDENT_GRAPH_BYTE_IDENTITY_AND_ISOLATION_GUARDS_PASS',checks)
if __name__=='__main__':main()
