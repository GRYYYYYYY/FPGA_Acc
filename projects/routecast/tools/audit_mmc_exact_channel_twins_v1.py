"""Independent Expat/additive-neighborhood certificate of no exact local twins.

Equal neighbor multisets necessarily have equal integer moments. If every
coarse metadata class has distinct signatures, absence is exact: no probabilistic
hash assumption is needed. Collisions would make the certificate inconclusive.
"""
import json,time,xml.parsers.expat as X
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_exact_channel_twins_v1_2026-10-21'
P=D/'verification.json';v=json.loads(P.read_text());assert v['exact_twin_classes']==0
G=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18/groups.json';groups=json.loads(G.read_text());graph=Path(next(p for p,h in v['bindings'].items() if Path(p).name=='rr_graph.xml'));assert groups['graph_sha256']==v['bindings'][str(graph)]
bindings={str(p):sha(p) for p in [Path(__file__),P,G]};bindings[str(graph)]=groups['graph_sha256'];index={};stats={};keys=[]
def freeze(x):return tuple(map(freeze,x)) if isinstance(x,list) else x
for i,g in enumerate(groups['groups']):
 keys.append(freeze(g['key']))
 for n,cap in g['members']:
  assert n not in index and cap>0;index[n]=(i,cap);stats[n]=[0]*6
assert len(index)==groups['channels']==v['positive_channels']
start=time.perf_counter();stack=[];current=None;seen=set();node_count=0;edge_count=0;attribute_names=set()
def begin(name,a):
 global current,edge_count
 parent=stack[-1] if stack else None;stack.append(name)
 if name=='node' and parent=='rr_nodes':
  n=int(a['id']);current={'a':dict(a),'id':n} if a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0 else None
 elif parent=='node' and current is not None and name in ['loc','segment','timing']:current[name]=dict(a)
 elif name=='edge' and parent=='rr_edges':
  if set(a)!={'src_node','sink_node','switch_id'}:raise ValueError('unsupported extra edge attributes')
  attribute_names.update(a);u=int(a['src_node']);w=int(a['sink_node']);s=int(a['switch_id']);edge_count+=1
  if not 0<=u<v['original_nodes'] or not 0<=w<v['original_nodes'] or not 0<=s<2**32:raise ValueError('edge domain')
  if u in stats:
   t=stats[u];x=(w<<32)+s;t[0]+=1;t[1]+=x;t[2]+=x*x
  if w in stats:
   t=stats[w];x=(u<<32)+s;t[3]+=1;t[4]+=x;t[5]+=x*x
 elif parent=='edge':raise ValueError('unsupported edge child data')
def end(name):
 global current,node_count
 parent=stack[-2] if len(stack)>1 else None
 if name=='node' and parent=='rr_nodes':
  if current is not None:
   n=current['id'];assert n in index and n not in seen;seen.add(n);a=current['a'];loc=dict(current['loc']);loc.pop('ptc',None);loc.setdefault('layer','0')
   key=(a['type'],a.get('direction'),tuple(sorted(loc.items())),tuple(sorted(current.get('segment',{}).items())),tuple(sorted(current.get('timing',{}).items())))
   gid,cap=index[n];assert keys[gid]==key and int(a['capacity'])==cap
  node_count+=1;current=None
 assert stack.pop()==name
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while block:=f.read(8*1024*1024):parser.Parse(block,False)
parser.Parse(b'',True)
assert seen==set(index) and node_count==v['original_nodes'] and edge_count==v['original_edges']
counts=Counter((index[n],tuple(row)) for n,row in stats.items());collisions=[c for c in counts.values() if c>1]
assert not collisions,'Integer moment certificate inconclusive; do not assert no twins from this audit'
assert all(sha(p)==h for p,h in bindings.items())
result={'status':'INDEPENDENT_EXACT_ABSENCE_CERTIFICATE_PASS','nodes_checked':node_count,'edges_checked':edge_count,'channels_checked':len(stats),'coarse_geometry_capacity_groups_validated':len(keys),'duplicate_integer_moment_signatures':0,'edge_attribute_names':sorted(attribute_names),'why_exact':'Exact same outgoing/incoming switch-multisets imply same counts and first/second integer moments. No two channels in any validated coarser geometry/capacity class share those moments; therefore no full-metadata exact-neighborhood twin exists. Hash collision assumptions are not used.','seconds':time.perf_counter()-start,'bindings':bindings,'scope':'No exact local row/column twins only; not absence of general graph automorphisms, cost-equivalent but switch-ID-different routes, or a prediction result.'}
(D/'independent_absence_certificate_v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)
