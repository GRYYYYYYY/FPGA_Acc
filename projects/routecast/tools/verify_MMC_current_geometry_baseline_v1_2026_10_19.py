"""Independent rectangle-difference density from native pin positions and XML capacities."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import json,hashlib,struct,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_current_geometry_baseline_v1_2026-10-19';receipt=O/'receipt.json';v=json.loads(receipt.read_text());assert v['status']=='ALL3_CURRENT_UNFITTED_BBOX_SPATIAL_BASELINES_PRODUCED';assert not (O/'independent_verification_v1.json').exists()
 for p,h in v['bindings'].items():assert sha(p)==h
 graph=next(Path(p) for p in v['bindings'] if p.endswith('rr_graph.xml'));capacity=Counter();direction=Counter();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
    loc=e.find('loc');seg=e.find('segment');layer=int(loc.get('layer','0'));segment=int(seg.get('segment_id')) if seg is not None else -1
    for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
     for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):key=layer,x,y,e.get('type'),segment;capacity[key]+=int(e.get('capacity'));direction[key[:4]]+=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(capacity)==17160;current_proof=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/independent_verification_v1.json';pin_proof=json.loads(current_proof.read_text());assert pin_proof['status']=='ALL3_CURRENT_INITIAL_TIMING_FLOAT32_PINS_XML_ENDPOINTS_NO_ROUTE_PASS';rows=[];bindings={str(p):sha(p) for p in [receipt,graph,current_proof,Path(__file__).resolve()]}
 for i in range(1,4):
  case=f'episode_{i:02d}';ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());idfile=Path(meta['inputs']['native_identity']['path']);assert sha(idfile)==meta['inputs']['native_identity']['sha256']==pin_proof['bindings'][str(idfile)];identity={x['net_id']:x for x in map(json.loads,idfile.read_text().splitlines())};counts=Counter(q['net_id'] for q in meta['connections']);assert len(counts)==55300 and sum(counts.values())==115572;diff=defaultdict(lambda:defaultdict(Fraction));maxx=max(k[1] for k in capacity);maxy=max(k[2] for k in capacity)
  for net,count in counts.items():
   native=identity[net];assert not native['ignored'] and len(native['pins'])==count+1;points=native['pins'];layers={p.get('layer',0) for p in points};assert len(layers)==1;layer=next(iter(layers));lo=min(p['x'] for p in points);hi=max(p['x'] for p in points);bottom=min(p['y'] for p in points);top=max(p['y'] for p in points);assert lo>=0 and bottom>=0;area=(hi-lo+1)*(top-bottom+1);maxx=max(maxx,hi);maxy=max(maxy,top)
   for kind,value in [('CHANX',Fraction(hi-lo,area)),('CHANY',Fraction(top-bottom,area))]:
    for x,y,sign in [(lo,bottom,1),(hi+1,bottom,-1),(lo,top+1,-1),(hi+1,top+1,1)]:diff[layer,kind][x,y]+=sign*value
  prefix={}
  for (layer,kind),raw in diff.items():
   values={}
   for x in range(maxx+1):
    for y in range(maxy+1):values[x,y]=raw.get((x,y),0)+values.get((x-1,y),0)+values.get((x,y-1),0)-values.get((x-1,y-1),0)
   prefix[layer,kind]=values
  payload=O/f'{case}.json';prediction=json.loads(payload.read_text());seen=set()
  for row in prediction['bins']:
   key=tuple(row['key']);assert key in capacity and key not in seen and row['capacity']==capacity[key];seen.add(key);layer,x,y,kind,segment=key;expected=float(prefix[layer,kind][x,y]/direction[key[:4]]);assert struct.pack('<d',row['value'])==struct.pack('<d',expected),(case,key,row['value'],expected)
  assert seen==set(capacity);rows.append({'case':case,'NETs':55300,'connections':115572,'all_spatial_values_bitwise_equal':17160,'method':'Native pin bbox rectangle corner updates + exact prefix sums; original XML capacity sums'});print('GEOMETRY_INDEPENDENT_PASS',case,flush=True)
  for p in [ep,idfile,payload]:bindings[str(p)]=sha(p)
 (O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL3_CURRENT_BBOX_GEOMETRY_NATIVE_PINS_XML_CAPACITY_DIFFERENCE_ARRAY_VALUES_PASS','rows':rows,'bindings':bindings,'scope':'Input-only spatial geometry baseline, no individual-resource/path/capacity feasibility claim or quality result.'},indent=2)+'\n')
if __name__=='__main__':main()
