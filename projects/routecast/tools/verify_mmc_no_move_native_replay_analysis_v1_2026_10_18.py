"""Independent printed-node, full XML-domain and histogram-metric validation."""
import ast,json,math,sys,time,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_no_move_native_replay_v1_2026-10-18';tick=time.perf_counter();rp=D/'repeatability_analysis_v1.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)}
vectors=json.loads((D/'repeatability_vectors.json').read_text());channels={x['node']:x for x in vectors['channels']};bins={tuple(x['key']):x for x in vectors['bins']};assert len(channels)==len(vectors['channels']) and len(bins)==len(vectors['bins'])
g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(g['previous_endpoint']).read_text());routes={'previous':Path(g['previous_native_route']),**{a:D/a/'output.route' for a in ['full_seed_a','cold','full_seed_b']}};truth={}
for label,route in routes.items():
 unions={};current=None;printed=0
 with route.open() as stream:
  for line in stream:
   words=line.split()
   if words and words[0]=='Net':
    current=int(words[1]) if line.rstrip().endswith(')') else None
    if current is not None:
     assert current not in unions;unions[current]=set()
   elif words and words[0]=='Node:':
    assert current is not None;unions[current].add(int(words[1]));printed+=1
 counts=Counter(n for nodes in unions.values() for n in nodes);assert sum(bool(x) for x in unions.values())==55300;truth[label]=counts
 if label!='previous':
  proof=json.loads((D/label/'physical_audit.json').read_text());assert proof['inputs_sha256']['route']==sha(route);assert dict(counts)=={int(n):v for n,v in proof['node_occupancy'].items()};assert printed==proof['printed_nodes']
source_dir=Path(ep['inputs']['net']['path']).parent
for arm in ['full_seed_a','cold','full_seed_b']:
 for name in ['design.blif','design.net','design.place']:
  original=source_dir/name;copy=D/arm/name;assert sha(original)==sha(copy);bindings[str(original)]=sha(original);bindings[str(copy)]=sha(copy)
seen=set();caps=Counter();tb={m:Counter() for m in truth};stack=[];graph=Path(ep['inputs']['graph']['path'])
for event,node in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(node);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if node.tag=='node' and parent=='rr_nodes':
  n=int(node.get('id'));capacity=int(node.get('capacity'));kind=node.get('type')
  if capacity>0 and kind in ('CHANX','CHANY'):
   assert n in channels and n not in seen;seen.add(n);c=channels[n];assert c['capacity']==capacity and c['counts']=={m:d.get(n,0) for m,d in truth.items()}
   loc=node.find('loc');segment=node.find('segment');seg=int(segment.get('segment_id')) if segment is not None else -1
   for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
     key=(int(loc.get('layer','0')),x,y,kind,seg);caps[key]+=capacity
     for m in truth:tb[m][key]+=truth[m].get(n,0)
  stack[-2].remove(node);node.clear()
 if node.tag=='rr_nodes':break
 stack.pop()
assert seen==set(channels) and set(caps)==set(bins)
for key,b in bins.items():assert b['capacity']==caps[key] and b['counts']=={m:tb[m][key] for m in truth}
audit_source=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';bindings[str(audit_source)]=sha(audit_source);fn=next(n for n in ast.parse(audit_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');ns=dict(Counter=Counter,math=math,checked=0);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(audit_source),'exec'),ns)
for arm in ['full_seed_a','cold','full_seed_b']:
 for scope,data,key,k in [('concrete',vectors['channels'],'node',max(1,len(channels)//20)),('spatial',vectors['bins'],'key',20)]:
  identity=lambda x:tuple(x[key]) if key=='key' else x[key]
  pv={identity(x):x['counts']['previous']/x['capacity'] for x in data};tv={identity(x):x['counts'][arm]/x['capacity'] for x in data};ns['audit_metric'](pv,tv,r['metrics_against_previous'][arm][scope],k)
assert ns['checked']==6
assert all(sha(p)==h for p,h in bindings.items())
with (D/'repeatability_independent_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,all4printed_NET_union_ledgers_verified=True,complete_positive_channel_and_spatial_domains_verified=True,histogram_metric_vectors_checked=6,positive_channels=len(channels),spatial_bins=len(bins),seconds=time.perf_counter()-tick,scope='Independent occupancy/domain/numerical verification; physical endpoint checks are provided by admitted native cohort, exact CID path reproducibility remains analyzer evidence.'),f,indent=2)
print('PASS independently replayed 4 route ledgers, XML domains and 6 metric vectors',flush=True)
