"""Full frozen model-pressure projection diagnostics, not search ablation."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from math import ceil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from direction_pressure_pool_v1 import PressurePool
out=R/'experiments/freecores_direction_pressure_component_v1_2026-10-08';out.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/direction_pressure_pool_v1.py'):sha(R/'tools/direction_pressure_pool_v1.py')};rows=[]
for name in ['8051','xtea']:
 endpoint=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(endpoint.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(endpoint)]=sha(endpoint);bindings[str(graph)]=ep['graph_sha256']
 nodes=list(ET.parse(graph).getroot().find('rr_nodes'));pools={mode:PressurePool(nodes,mode) for mode in ['within_polarity','across_polarity']};positive={n for n,node in enumerate(nodes) if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0};nonchannel=set(range(len(nodes)))-positive
 for mode,pool in pools.items():
  seen=set()
  for group in pool.groups:
   assert len(group)==len(set(group)) and not seen.intersection(group);seen.update(group)
   keys=[];dirs=set()
   for n in group:
    node=nodes[n];loc=node.find('loc');keys.append((node.get('type'),node.get('capacity'),tuple(loc.get(k,'0') for k in ['xlow','xhigh','ylow','yhigh','layer']),ET.tostring(node.find('segment')),ET.tostring(node.find('timing'))));dirs.add(node.get('direction'))
   assert all(key==keys[0] for key in keys)
   if mode=='within_polarity':assert len(dirs)==1
   else:assert dirs=={'INC_DIR','DEC_DIR'}
  assert seen==positive
 for index in range(2):
  state=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident'/f'round{index}.json';d=json.loads(state.read_text());bindings[str(state)]=sha(state);prices={int(k):v for k,v in d['prices'].items()};outputs={}
  for mode,pool in pools.items():
   projected=pool.project(prices)
   for group in pool.groups:
    expected=ceil(sum((Fraction(prices.get(n,0)) for n in group),Fraction())/len(group));assert all(projected.get(n,0)==expected for n in group)
   assert all(projected.get(n,0)==prices.get(n,0) for n in nonchannel)
   target=out/(name+'_'+str(index)+'_'+mode+'.json');target.write_text(json.dumps(dict(prices=projected),sort_keys=True)+'\n');bindings[str(target)]=sha(target);outputs[mode]=projected
  within,across=[outputs[m] for m in ['within_polarity','across_polarity']]
  rows.append(dict(name=name,round_index=index,positive_channels=len(positive),within_groups=len(pools['within_polarity'].groups),across_groups=len(pools['across_polarity'].groups),raw_to_within_changed=sum(within.get(n,0)!=prices.get(n,0) for n in positive),within_to_across_changed=sum(within.get(n,0)!=across.get(n,0) for n in positive),all_metadata_groups_positive_coverage_and_fraction_ceiling_and_nonchannel_prices_pass=True))
assert all(sha(k)==h for k,h in bindings.items())
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Full original two-round model prices projected after the fact, all physical graph/arcs/RC/labels untouched. Within mode pools tracks while retaining polarity; across additionally removes polarity distinction. Actual re-search, affected-node closure and outcome/accuracy/native QoR remain untested; not topology-direction ablation or prospective unseen evidence.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
