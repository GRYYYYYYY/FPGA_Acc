"""Untuned directional bbox density projected to channel utilization proxy."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from prediction_metrics import spearman
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_crossbar_soft_metrics_2026-10-06';p=json.loads((base/'protocol.json').read_text());out=root/'experiments/mux_bbox_control_2026-10-06';out.mkdir();cases=[]
for c in p['cases']:
 w=c['data_width'];ch=c['channels'];source=json.loads((root/'experiments/mux_crossbar_soft_transfer_2026-10-06/protocol.json').read_text());item=next(x for x in source['cases'] if x['data_width']==w and x['channels']==ch);ep=Path(item['endpoint_path']);assert sha(ep)==item['endpoint_sha256'];cases.append({**c,'endpoint_path':str(ep),'endpoint_sha256':sha(ep)})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'source_sha256':sha(Path(__file__)),'definition':'UniqueNET endpoint RR xlow/ylow bbox. Uniform CHANX dx/area and CHANY dy/area density. Divide by all channelcapacity ineachdirection atcell, thenaveragecell utilization along eachRRrectangle. No fittedparameter. Resourceutilizationproxy not physicalpath/NEToccupancy.','scope':'Posthoc samefulluniverse baseline. Generateall9beforeopeningnativevectors; all9 complete softcomparisons. Singlelayerarchitectureonly.'},indent=2)+'\n');predictions={}
for c in cases:
 ep=json.loads(Path(c['endpoint_path']).read_text());x=ET.parse(c['graph']).getroot();nodes={int(n.get('id')):n for n in x.find('rr_nodes')};groups=defaultdict(set);density=defaultdict(Fraction);capacity=defaultdict(int);channels={}
 for q in ep['connections']:groups[q['net_id']].update((q['source'],q['sink']))
 for group in groups.values():
  pts=[nodes[n].find('loc').attrib for n in group];assert all(int(loc.get('layer','0'))==0 for loc in pts);xs=[int(loc['xlow']) for loc in pts];ys=[int(loc['ylow']) for loc in pts];lo,hi=min(xs),max(xs);bottom,top=min(ys),max(ys);area=(hi-lo+1)*(top-bottom+1)
  for xx in range(lo,hi+1):
   for yy in range(bottom,top+1):density[xx,yy,'CHANX']+=Fraction(hi-lo,area);density[xx,yy,'CHANY']+=Fraction(top-bottom,area)
 for n,node in nodes.items():
  kind=node.get('type');cap=int(node.get('capacity'))
  if kind not in ('CHANX','CHANY') or cap<=0:continue
  loc=node.find('loc').attrib;assert int(loc.get('layer','0'))==0;cells=[(xx,yy,kind) for xx in range(int(loc['xlow']),int(loc['xhigh'])+1) for yy in range(int(loc['ylow']),int(loc['yhigh'])+1)];channels[n]=cells
  for cell in cells:capacity[cell]+=cap
 util={n:sum(density[cell]/capacity[cell] for cell in cells)/len(cells) for n,cells in channels.items()};file=out/f"gf2_d{c['data_width']}_w{c['channels']}_vectors.json";file.write_text(json.dumps([{'node':n,'utilization_fraction':str(util[n])} for n in sorted(util)],indent=2)+'\n');predictions[c['data_width'],c['channels']]=(util,sha(file));assert sha(c['endpoint_path'])==c['endpoint_sha256']
# Labels read only after all predictions have been generated.
soft=json.loads((base/'receipt.json').read_text());rows=[]
for c,s in zip(cases,soft['rows']):
 w=c['data_width'];ch=c['channels'];util,digest=predictions[w,ch]
 if not c['complete']:rows.append({'data_width':w,'channels':ch,'scored':False,'prediction_sha256':digest});continue
 data=json.loads((base/f'gf2_d{w}_w{ch}_vectors.json').read_text());assert sha(base/f'gf2_d{w}_w{ch}_vectors.json')==s['vector_sha256'];ids=[v['node'] for v in data];assert ids==sorted(util);truth=[v['native']/v['capacity'] for v in data];pred=[float(util[n]) for n in ids];row={'data_width':w,'channels':ch,'scored':True,'bbox_resource_proxy_spearman':spearman(pred,truth),'bbox_resource_proxy_MAE':sum(abs(a-b) for a,b in zip(pred,truth))/len(ids),'soft_resource_spearman':s['utilization_spearman'],'soft_resource_MAE':s['utilization_MAE'],'prediction_sha256':digest};rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'soft_receipt_sha256':sha(base/'receipt.json'),'rows':rows,'scope':'Uncalibrated bbox channelutilizationproxy vs identicalnativechanneluniverse; no nativefailurethreshold or physicalroute claim. Independent bbox arithmetic audit still pending.'},indent=2)+'\n')
