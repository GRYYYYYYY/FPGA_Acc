"""Authenticate all endpoint inputs and check every RR node RC plus all switches."""
from pathlib import Path
from fractions import Fraction
from math import lcm
from collections import Counter
import xml.etree.ElementTree as ET,json,time
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_electrical_qualification_v1_2026-10-10';O.mkdir(exist_ok=True)
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';v=json.loads(ep.read_text());bindings={str(ep):sha(ep),str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')}
for x in v['inputs'].values():assert sha(x['path'])==x['sha256'];bindings[x['path']]=x['sha256']
graph=Path(v['inputs']['graph']['path']);assert bindings[str(graph)]==v['graph_sha256'];start=time.perf_counter();switches={};classes=Counter();nodes=0;capacities=Counter();parent=None
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':
  if e.tag=='rr_nodes':parent=e
  continue
 if e.tag=='switch':
  t=e.find('timing');sid=int(e.get('id'));assert sid not in switches and t is not None
  assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0
  switches[sid]=dict(R=Fraction(t.get('R','0')),Tdel=Fraction(t.get('Tdel','0')))
 elif e.tag=='node' and parent is not None:
  assert int(e.get('id'))==nodes;t=e.find('timing');assert t is not None and 'R' in t.attrib and 'C' in t.attrib
  key=(t.get('R'),t.get('C'));classes[key]+=1;capacities[int(e.get('capacity'))]+=1;nodes+=1;e.clear()
  if nodes%1024==0:parent.clear()
 elif e.tag=='rr_nodes':break
assert nodes and switches and sum(classes.values())==nodes
all_zero=all(Fraction(r)==Fraction(c)==0 for r,c in classes)
scale=lcm(1,*(x['Tdel'].denominator for x in switches.values()))
costs={sid:int(x['Tdel']*scale) for sid,x in switches.items()};current={0:0,1:129999997,2:207900003,3:312900011}
assert all(sha(p)==h for p,h in bindings.items());qs=v['connections'];groups={}
for q in qs:
 assert 0<=q['source']<nodes and 0<=q['sink']<nodes;groups.setdefault(q['net_id'],[]).append(q)
assert all(len({q['source'] for q in g})==1 for g in groups.values())
result=dict(bindings=bindings,nodes=nodes,capacities=dict(capacities),node_electrical_classes=[dict(R=r,C=c,count=count) for (r,c),count in classes.items()],all_node_R_and_C_zero=all_zero,switch_scale=scale,switch_costs=costs,current_native_switch_costs_exact_equal=costs==current,current_native_scale_equal=scale==10**18,queries=len(qs),nets=len(groups),prefix_scan_seconds=time.perf_counter()-start,scope='Every node and every switch electrical metadata checked in authenticated original XML prefix. Not full topology/globaledge/native pin/route/floors verification, not native execution or heldout evidence.')
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','node_electrical_classes']})
