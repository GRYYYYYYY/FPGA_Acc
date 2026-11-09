"""Independent per-resource rectangle density oracle and exact-rank comparison."""
import json,math,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_bbox_control_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());base=root/'experiments/mux_crossbar_soft_metrics_2026-10-06';assert r['protocol_sha256']==sha(out/'protocol.json') and p['source_sha256']==sha(root/'tools/trial_mux_bbox_control.py');assert r['soft_receipt_sha256']==sha(base/'receipt.json');soft=json.loads((base/'receipt.json').read_text());sv=json.loads((base/'verification.json').read_text());assert sv['receipt_sha256']==sha(base/'receipt.json')
def rho(x,y):
 def ranks(v):
  groups=defaultdict(list)
  for i,n in enumerate(v):groups[n].append(i)
  result=[None]*len(v);offset=0
  for value in sorted(groups):
   indices=groups[value];mid=Fraction(2*offset+len(indices)-1,2)
   for i in indices:result[i]=mid
   offset+=len(indices)
  return result
 a,b=ranks(x),ranks(y);mean=Fraction(len(a)-1,2);va=sum((v-mean)**2 for v in a);vb=sum((v-mean)**2 for v in b);return None if not va or not vb else float(sum((x-mean)*(y-mean) for x,y in zip(a,b)))/math.sqrt(float(va*vb))
rows=[]
for c,row,s in zip(p['cases'],r['rows'],soft['rows']):
 w=c['data_width'];ch=c['channels'];assert (w,ch)==(row['data_width'],row['channels'])==(s['data_width'],s['channels']);assert sha(c['endpoint_path'])==c['endpoint_sha256'] and all(sha(f)==h for f,h in c['bindings'].items());ep=json.loads(Path(c['endpoint_path']).read_text());assert sha(ep['inputs']['graph']['path'])==ep['graph_sha256'];x=ET.parse(c['graph']).getroot();nodes={int(n.get('id')):n for n in x.find('rr_nodes')};rects={};directional=defaultdict(int)
 for n,node in nodes.items():
  kind=node.get('type');cap=int(node.get('capacity'))
  if kind not in ('CHANX','CHANY') or cap<=0:continue
  loc=node.find('loc').attrib;assert int(loc.get('layer','0'))==0;cells={(xx,yy) for xx in range(int(loc['xlow']),int(loc['xhigh'])+1) for yy in range(int(loc['ylow']),int(loc['yhigh'])+1)};rects[n]=(kind,cells)
  for xx,yy in cells:directional[xx,yy,kind]+=cap
 nets=defaultdict(set)
 for q in ep['connections']:nets[q['net_id']].update((q['source'],q['sink']))
 boxes=[]
 for terminals in nets.values():
  coords=[(int(nodes[n].find('loc').get('xlow')),int(nodes[n].find('loc').get('ylow'))) for n in terminals];xs,ys=zip(*coords);boxes.append((min(xs),max(xs),min(ys),max(ys)))
 # Per-resource oracle integrates each NET intersection directly, instead of
 # production's cell-density accumulation, then exact arithmetic averages cells.
 expected={}
 for n,(kind,cells) in rects.items():
  value=Fraction(0)
  for lo,hi,bottom,top in boxes:
   span=hi-lo if kind=='CHANX' else top-bottom;area=(hi-lo+1)*(top-bottom+1)
   if not span:continue
   value+=sum(Fraction(span,area*directional[xx,yy,kind]) for xx,yy in cells if lo<=xx<=hi and bottom<=yy<=top)
  expected[n]=value/len(cells)
 file=out/f'gf2_d{w}_w{ch}_vectors.json';assert sha(file)==row['prediction_sha256'];vectors=json.loads(file.read_text());assert vectors==[{'node':n,'utilization_fraction':str(expected[n])} for n in sorted(expected)]
 checked={'data_width':w,'channels':ch,'proxy_vectors_verified':len(expected),'scored':row['scored']}
 if row['scored']:
  sf=base/f'gf2_d{w}_w{ch}_vectors.json';assert sha(sf)==s['vector_sha256'];native=json.loads(sf.read_text());assert [v['node'] for v in native]==sorted(expected);truth=[Fraction(v['native'],v['capacity']) for v in native];values=[expected[v['node']] for v in native];rr=rho(values,truth);assert math.isclose(rr,row['bbox_resource_proxy_spearman'],abs_tol=1e-12);mae=float(sum(abs(a-b) for a,b in zip(values,truth))/len(values));assert math.isclose(mae,row['bbox_resource_proxy_MAE'],abs_tol=1e-12);assert row['soft_resource_spearman']==s['utilization_spearman'] and row['soft_resource_MAE']==s['utilization_MAE'];checked.update(bbox_resource_proxy_spearman=rr,bbox_MAE=mae,soft_higher_rho=s['utilization_spearman']>rr,soft_lower_MAE=s['utilization_MAE']<mae)
 else:assert not c['complete']
 rows.append(checked);print(w,ch,'bbox oracle verified',flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'All9 originalXML capacities/endpointNETbbox and per-resource intersectionFractionintegration checked,6 exactrank/MAE comparisons authenticated. No physicalroute, calibratedpressure/failureclassifier, independentfamily or end-to-endgain proof.'},indent=2)+'\n')
