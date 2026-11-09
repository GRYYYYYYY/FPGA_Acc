"""Independent min-Chebyshev-distance selection replay from old XML/route."""
import json,sys,re,xml.etree.ElementTree as E
from pathlib import Path
from array import array
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_old_route_spatial_context_v1_2026-10-18';sp=D/'selection.json';s=json.loads(sp.read_text());P=json.loads((D/'protocol.json').read_text());assert P['radii']==[0,1,2,4,8] and P['primary_radius']==2;bindings={**s['bindings'],**closure([Path(__file__)]),str(sp):sha(sp)};assert all(sha(p)==h for p,h in bindings.items())
g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());old=json.loads(Path(g['previous_endpoint']).read_text());graph=Path(old['inputs']['graph']['path']);assert sha(graph)==old['graph_sha256']==old['inputs']['graph']['sha256'];names={old['net_names'][str(q['net_id'])]:q['net_id'] for q in old['connections']};cases=['case_01','case_02','case_03'];INF=65535;centers={case:next(x['centers'] for x in P['specs'] if x['case']==case) for case in cases};distances={c:array('H') for c in cases};stack=[]
for event,e in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  nid=int(e.get('id'))
  for c in cases:assert len(distances[c])==nid;distances[c].append(INF)
  if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
   loc=e.find('loc');xl,xh,yl,yh=(int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']);layer=int(loc.get('layer','0'))
   for c in cases:
    possible=[max(max(xl-x,0,x-xh),max(yl-y,0,y-yh)) for x,y,z in centers[c] if z==layer]
    if possible:distances[c][nid]=min(possible)
  stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
minimum={c:{n:INF for n in names} for c in cases};seen=set();current=None;header=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)(.*)$')
for line in Path(g['previous_native_route']).open():
 m=header.match(line)
 if m:
  current=m[2] if not m[3].strip() else None
  if current is not None:assert current in names and current not in seen;seen.add(current)
 elif line.lstrip().startswith('Node:'):
  assert current in names;n=int(line.split()[1])
  for c in cases:minimum[c][current]=min(minimum[c][current],distances[c][n])
assert seen==set(names);rows=[]
for c in cases:
 previous=set()
 for radius in P['radii']:
  spec=next(x for x in P['specs'] if x['case']==c and x['radius']==radius);expected=set(spec['endpoint_NET_closure'])|{names[n] for n,d in minimum[c].items() if d<=radius};actual=next(x for x in s['rows'] if x['case']==c and x['radius']==radius);assert expected==set(actual['net_ids']) and len(expected)==actual['NETs'] and previous<=expected;previous=expected;rows.append(dict(case=c,radius=radius,NETs=len(expected)))
assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_selection_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all15_NET_sets_equal_independent_original_XML_min_distance_replay=True,monotone_radius_sets=True,scope='Independent distance formulation and route/header traversal, using old native source only. Does not independently re-run geometry first-eligible selection or assess target labels/quality.'),f,indent=2)
print('PASS15 originalXML/oldroute context selections',flush=True)
