"""Frozen simple endpoint-bbox spatial control, no physical search or labels.
One net contributes x-span and y-span uniformly over its inclusive bbox.
Demand is split over segments proportional to available directional capacity.
This declared development baseline is not a calibrated routability model.
"""
import json,time,shutil
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha

out=Path('experiments/koios_geometry_control_2026-10-05')
if out.exists():raise ValueError('fresh output required')
parent=Path('experiments/koios_cpp_resume_2026-10-05/protocol.json');prior=json.loads(parent.read_text())
inputs={k:prior['inputs'][k] for k in ['rr_graph.xml','endpoints']}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
e=json.loads(Path(inputs['endpoints']['path']).read_text());assert len(e['connections'])==15138
groups=defaultdict(set)
for r in e['connections']:groups[(r['net_id'],r['source'])].update([r['source'],r['sink']])
assert len(groups)==8998
wanted={n for v in groups.values() for n in v};locations={};capacities=defaultdict(int);directional=defaultdict(int)
out.mkdir();(out/'source').mkdir();shutil.copy2(__file__,out/'source'/Path(__file__).name)
protocol={'inputs':inputs,'source_sha256':sha(__file__),'scope':'simple geometry spatial control only; no paths, node-resource accuracy or routing feasibility claim','definition':'endpoint RR xlow/ylow anchors; per-net inclusive bbox area; uniform CHANX demand dx/area, CHANY dy/area; segment split proportional to directional capacity; no fitted weights','zero_span':'zero geometric demand for same-coordinate net; local pin/switch usage intentionally outside this estimator','cohort':'all8998SOURCEgroups/15138connections, unique-net contribution','evaluation':'same spatial x,y,type,segment capacity bins as physical predictor; top20, Spearman, MAE and original string-key tie rule','labels':'native labels never opened by predictor'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();stack=[]
for event,node in ET.iterparse(inputs['rr_graph.xml']['path'],events=('start','end')):
 if event=='start':stack.append(node);continue
 if node.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
  nid=int(node.attrib['id']);kind=node.attrib['type'];cap=int(node.attrib['capacity']);loc=node.find('loc').attrib
  if nid in wanted:locations[nid]=(int(loc['xlow']),int(loc['ylow']))
  if kind in {'CHANX','CHANY'} and cap:
   segment=node.find('segment').attrib['segment_id']
   for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
     capacities[f'{x},{y},{kind},{segment}']+=cap;directional[(x,y,kind)]+=cap
  stack[-2].remove(node);node.clear()
 if node.tag=='rr_nodes':break
 stack.pop()
assert wanted==set(locations)
demand=defaultdict(Fraction);zero=0
for nodes in groups.values():
 points=[locations[n] for n in nodes];lo=min(x for x,y in points);hi=max(x for x,y in points);bottom=min(y for x,y in points);top=max(y for x,y in points);dx=hi-lo;dy=top-bottom;area=(dx+1)*(dy+1);zero+=dx==dy==0
 for x in range(lo,hi+1):
  for y in range(bottom,top+1):
   demand[(x,y,'CHANX')]+=Fraction(dx,area);demand[(x,y,'CHANY')]+=Fraction(dy,area)
values={}
for key in capacities:
 x,y,kind,seg=key.split(',');k=(int(x),int(y),kind);values[key]=float(demand[k]/directional[k])
(out/'spatial_prediction.json').write_text(json.dumps(values)+'\n');(out/'spatial_capacities.json').write_text(json.dumps(dict(capacities))+'\n')
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
receipt={'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(out/'source'/Path(__file__).name),'inputs_unchanged':True,'nets':len(groups),'connections':len(e['connections']),'spatial_bins':len(values),'same_coordinate_nets':zero,'prediction_s':time.monotonic()-start,'outputs':{f:sha(out/f) for f in ['spatial_prediction.json','spatial_capacities.json']},'scope':protocol['scope']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
