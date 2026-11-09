"""Unchanged existing perNET endpoint bbox baseline, current3 spatial domain only."""
from pathlib import Path
from types import SimpleNamespace
import json,hashlib,time,resource,xml.etree.ElementTree as ET
from endpoint_bbox_demand_v1 import predict
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));O=R/'experiments/mmc_current_geometry_baseline_v1_2026-10-19';O.mkdir(exist_ok=False);cases=[f'episode_{i:02d}' for i in range(1,4)];eps={case:R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json' for case in cases};meta={case:json.loads(p.read_text()) for case,p in eps.items()};graph=Path(meta[cases[0]]['inputs']['graph']['path']);assert all(x['graph_sha256']==sha(graph) for x in meta.values());wanted={q[k] for x in meta.values() for q in x['connections'] for k in ['source','sink']};model_protocol=R/'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19/protocol.json';registered=json.loads(model_protocol.read_text());baseline=R/'tools/endpoint_bbox_demand_v1.py';assert sha(baseline)==registered['bindings'][str(baseline)];bindings={str(p):sha(p) for p in [graph,baseline,model_protocol,Path(__file__).resolve(),*eps.values()]};(O/'protocol.json').write_text(json.dumps({'bindings':bindings,'cases':cases,'definition':'Existing endpoint_bbox_demand_v1: perNET uniform bbox dx/area CHANX and dy/area CHANY demand, direction-capacity split over segments; zero-span0, no fitted parameters.','scope':'Spatial17160 bins only; no individual-resource accuracy, path legality or routability claim. No native target route labels. May run concurrently with model; component clocks not a fresh sequential workflow.'},indent=2)+'\n');nodes={};stack=[];tick=time.perf_counter()
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   n=int(e.get('id'));kind=e.get('type');cap=int(e.get('capacity'))
   if n in wanted or kind in ['CHANX','CHANY'] and cap>0:
    seg=e.find('segment');nodes[n]=SimpleNamespace(type=kind,capacity=cap,location=tuple(e.find('loc').attrib.items()),segment_id=int(seg.get('segment_id')) if seg is not None else None)
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert wanted<=set(nodes);geometry_load_seconds=time.perf_counter()-tick;rows=[]
 for case in cases:
  tick=time.perf_counter();values,caps=predict(nodes,meta[case]['connections']);seconds=time.perf_counter()-tick;assert set(values)==set(caps) and len(values)==17160;p=O/f'{case}.json';p.write_text(json.dumps({'case':case,'connections':115572,'bins':[{'key':list(k),'capacity':caps[k],'value':values[k]} for k in sorted(values)]},separators=(',',':'))+'\n');bindings[str(p)]=sha(p);rows.append({'case':case,'spatial_bins':len(values),'baseline_seconds':seconds});print('CURRENT_GEOMETRY_DONE',case,seconds,flush=True)
 (O/'receipt.json').write_text(json.dumps({'status':'ALL3_CURRENT_UNFITTED_BBOX_SPATIAL_BASELINES_PRODUCED','rows':rows,'graph_geometry_seconds':geometry_load_seconds,'total_before_receipt_seconds':time.perf_counter()-begin,'bindings':bindings,'independent_verification_pending':True,'scope':'Spatial-only, input-only existing baseline, no native labels read or changed parameters.'},indent=2)+'\n')
if __name__=='__main__':main()
