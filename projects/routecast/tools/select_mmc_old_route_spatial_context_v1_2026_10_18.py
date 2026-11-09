"""Freeze old-route spatial NET contexts without reading target route labels."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
G=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18';proof=G/'geometry_independent_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='pass' and all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],**closure([Path(__file__)]),str(proof):sha(proof)}
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());ep=Path(g['previous_endpoint']);old=json.loads(ep.read_text());route=Path(g['previous_native_route']);graph=Path(old['inputs']['graph']['path']);names={old['net_names'][str(q['net_id'])]:q['net_id'] for q in old['connections']};assert len(names)==55300
D=R/'experiments/mmc_old_route_spatial_context_v1_2026-10-18';D.mkdir();radii=[0,1,2,4,8];specs=[]
for case in ['case_01','case_02','case_03']:
 pp=G/case/'protocol.json';sel=json.loads(pp.read_text())['selected'];centers=sorted({(p[0],p[1],p[3]) for p in sel['before_positions'].values()});ip=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'staged_input_verification_v1.json';iv=json.loads(ip.read_text());assert all(sha(p)==h for p,h in iv['bindings'].items());bindings[str(pp)]=sha(pp);bindings[str(ip)]=sha(ip)
 for radius in radii:specs.append(dict(case=case,radius=radius,centers=centers,endpoint_NET_closure=iv['affected']['affected_net_ids']))
for p in [gp,ep,route,graph]:bindings[str(p)]=sha(p)
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,radii=radii,primary_radius=2,specs=specs,selection='Union endpoint NET closure with every physical-demand NET whose accepted old native route contains a positive-capacity CHANX/CHANY segment intersecting the inclusive Chebyshev-radius box of a swapped block site on the same layer. All query NET members included. No new route labels or quality metrics used.',scope='Old-input context selection and cost/coverage diagnosis on already exposed layouts. Radius2 registered for mechanism exploration before coverage computation, other radii diagnostic only; not a new unseen quality confirmation or promotion gate.'),f,indent=2)
mask={};stack=[]
for event,node in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(node);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if node.tag=='node' and parent=='rr_nodes':
  if node.get('type') in ['CHANX','CHANY'] and int(node.get('capacity'))>0:
   loc=node.find('loc');lo=(int(loc.get('xlow')),int(loc.get('ylow')));hi=(int(loc.get('xhigh')),int(loc.get('yhigh')));layer=int(loc.get('layer','0'));bits=0
   for index,s in enumerate(specs):
    r=s['radius']
    if any(z==layer and lo[0]<=x+r and hi[0]>=x-r and lo[1]<=y+r and hi[1]>=y-r for x,y,z in s['centers']):bits|=1<<index
   if bits:mask[int(node.get('id'))]=bits
  stack[-2].remove(node);node.clear()
 if node.tag=='rr_nodes':break
 stack.pop()
netbits={n:0 for n in names};current=None
with route.open() as stream:
 for line in stream:
  words=line.split()
  if words and words[0]=='Net':current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
  elif words and words[0]=='Node:':assert current in names;netbits[current]|=mask.get(int(words[1]),0)
fanout=Counter(q['net_id'] for q in old['connections']);rows=[]
for index,s in enumerate(specs):
 nets=set(s['endpoint_NET_closure'])|{names[n] for n,bits in netbits.items() if bits&(1<<index)};row=dict(case=s['case'],radius=s['radius'],net_ids=sorted(nets),NETs=len(nets),connections=sum(fanout[n] for n in nets),endpoint_NET_closure_count=len(s['endpoint_NET_closure']));rows.append(row);print('CONTEXT',row['case'],row['radius'],row['NETs'],row['connections'],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'selection.json').open('x') as f:json.dump(dict(bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},rows=rows,independent_selection_audit_pending=True,no_target_route_or_quality_values_read=True),f,indent=2)
