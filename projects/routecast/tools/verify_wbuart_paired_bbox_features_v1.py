"""Independent Fraction rectangular masses/capacities and full38 byte prefixes."""
import json,struct,math
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_paired_bbox_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==9 and not v['target_labels_read'] and len(v['columns'])==41 and all(sha(path)==h for path,h in v['bindings'].items());H=read(E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json');graph_cache={};old_cache={};count=0;max_error=0;rows=[]
 for r in v['rows']:
  info=next(x for x in H['rows'] if x['case']==r['case']);digest=info['graph_sha256']
  if digest not in graph_cache:
   nodes={n['id']:n for n in map(json.loads,Path(E/'wbuart_preroute_heterograph_v1_2026-10-20/graphs'/digest/'RR_nodes.jsonl').read_text().splitlines())};capacities=Counter()
   for node in nodes.values():
    if node['type'] not in ['CHANX','CHANY'] or node['capacity']<=0:continue
    loc=node['loc']
    for x in range(loc['xlow'],loc['xhigh']+1):
     for y in range(loc['ylow'],loc['yhigh']+1):capacities[loc.get('layer',0),x,y,node['type']]+=node['capacity']
   graph_cache[digest]=(nodes,capacities)
  nodes,capacities=graph_cache[digest];ids=read(r['resource_ids'])
  def exact(queries):
   endpoints=defaultdict(set);demand=defaultdict(F)
   for q in queries:endpoints[q['net_id']].update([q['source'],q['sink']])
   for members in endpoints.values():
    locations=[nodes[n]['loc'] for n in members];layers={loc.get('layer',0) for loc in locations};assert len(layers)==1;layer=next(iter(layers));xs=[loc['xlow'] for loc in locations];ys=[loc['ylow'] for loc in locations];xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys);dx,dy=xmax-xmin,ymax-ymin;area=(dx+1)*(dy+1)
    for x in range(xmin,xmax+1):
     for y in range(ymin,ymax+1):demand[layer,x,y,'CHANX']+=F(dx,area);demand[layer,x,y,'CHANY']+=F(dy,area)
   result={}
   for n in ids:
    node=nodes[n];loc=node['loc'];values=[demand[loc.get('layer',0),x,y,node['type']]/capacities[loc.get('layer',0),x,y,node['type']] for x in range(loc['xlow'],loc['xhigh']+1) for y in range(loc['ylow'],loc['yhigh']+1)];result[n]=sum(values,F(0))/len(values)
   return result
  if r['source_frame'] not in old_cache:old_cache[r['source_frame']]=exact(read(r['source_frame'])['records'])
  before_exact=old_cache[r['source_frame']];after_exact=exact(list(map(json.loads,Path(r['target_incidence']).read_text().splitlines())));original=Path(r['original38_matrix']).read_bytes();blob=Path(r['matrix']).read_bytes();assert len(original)==304*len(ids) and len(blob)==328*len(ids);ledger={int(n):c for n,c in read(r['source_frame'])['ledger'].items()};numeric_changed=0;empty_changed=0;rounding_only=0;math_changed=0;math_empty=0
  for i,n in enumerate(ids):
   assert blob[i*328:i*328+304]==original[i*304:(i+1)*304];a,b,d=struct.unpack('<3d',blob[i*328+304:(i+1)*328]);assert d==b-a
   for got,expected in [(a,before_exact[n]),(b,after_exact[n])]:
    error=abs(got-float(expected));max_error=max(max_error,error);assert error<=1e-12*max(1,abs(float(expected)))
   numeric_changed+=d!=0;empty_changed+=not ledger.get(n,0) and d!=0;math_changed+=before_exact[n]!=after_exact[n];math_empty+=not ledger.get(n,0) and before_exact[n]!=after_exact[n];rounding_only+=d!=0 and before_exact[n]==after_exact[n];count+=1
  assert numeric_changed==r['paired_bbox_delta_nonzero_resources'] and empty_changed==r['previously_unoccupied_with_nonzero_delta'];rows.append({'case':r['case'],'numeric_delta_rows':numeric_changed,'exact_rational_delta_rows':math_changed,'previously_unoccupied_exact_delta_rows':math_empty,'rounding_only_nonzero_delta_rows':rounding_only});print('PAIRED_BBOX_INPUT_VERIFIED',r['case'],math_changed,math_empty,rounding_only,flush=True)
 out=D/'independent_verification_v1.json';out.write_text(json.dumps({'status':'ALL9_FRACTION_PAIRED_BBOX_REFERENCE_AND38_BYTE_PREFIXES_VERIFIED','resource_rows':count,'maximum_float_reference_error':max_error,'rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Existing helper floating mean checked against exact rational proxy. Rounding-only rows reported, not evidence of physical signal. No target labels/model/forecast quality/native admission.'},indent=2)+'\n');print('ALL_PAIRED_BBOX_INPUTS_VERIFIED',count,max_error)
if __name__=='__main__':main()
