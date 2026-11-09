"""Posthoc descriptive spatial-bias diagnosis; no predictor changes or tuning."""
import json,shutil,math
from pathlib import Path
from collections import Counter,defaultdict
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from native_node_labels import node_labels
from pin_template_trial import spatial
out=Path('experiments/clma_spatial_diagnosis_2026-10-04')
if out.exists():raise ValueError('fresh output required')
prior=json.loads(Path('experiments/clma_normalized_transfer_evaluation_2026-10-04/protocol.json').read_text());inputs=prior['inputs']
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'posthoc descriptive diagnosis after known hotspot failure, no model/weight/selection changes; same already-developed clma','checks':['original top20 coordinates/direction and distance to observed orientation/segment domain boundary','rank of native top20 under predictions','spatial demand centroid','per-channel direction touch totals and span histogram weighted by net occupancy','occupied weighted node R/C means'],'k':20,'tie_rule':'descending density then ascending string spatial key, as original evaluator','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');g=read_rr_graph(inputs['graph']['path']);truth=node_labels(g,inputs['route']['path'],inputs['place']['sha256']);loads={'native':truth}
for name in ('length_switch','blend','own_excluded_pressure'):loads[name]=json.loads(Path(inputs[name]['path']).read_text())['node_occupancy']
spatial_maps={name:spatial(g,v) for name,v in loads.items()};keys=list(spatial_maps['native']);domains=defaultdict(list)
def decode(key):
 x,y,kind,segment=key.split(',');return int(x),int(y),kind,segment
for key in keys:
 x,y,kind,segment=decode(key);domains[(kind,segment)].append((x,y))
bounds={k:(min(x for x,y in pts),max(x for x,y in pts),min(y for x,y in pts),max(y for x,y in pts)) for k,pts in domains.items()}
def distance(key):
 x,y,kind,segment=decode(key);lo,hi,bottom,top=bounds[(kind,segment)];return min(x-lo,hi-x,y-bottom,top-y)
def ranking(values):return sorted(values,key=lambda k:(-values[k],k))
native_top=ranking(spatial_maps['native'])[:20];summaries={};top_records={}
for name,values in loads.items():
 density=spatial_maps[name];ranked=ranking(density);positions={k:i+1 for i,k in enumerate(ranked)};top=ranked[:20];weights=sum(density.values())
 directions=Counter();spans=Counter();touches=0;r_weight=0.;c_weight=0.
 for nid,node in g.nodes.items():
  if node.type not in {'CHANX','CHANY'} or not node.capacity:continue
  count=values.get(str(nid),0)
  loc=dict(node.location);span=int(loc['xhigh'])-int(loc['xlow'])+int(loc['yhigh'])-int(loc['ylow'])+1
  directions[node.type+':'+node.direction]+=count;spans[span]+=count;touches+=count
  t=dict(node.timing);r_weight+=count*float(t['R']);c_weight+=count*float(t['C'])
 summary={'top20_overlap_native':len(set(top)&set(native_top)),'top20_mean_boundary_distance':sum(distance(k) for k in top)/20,'top20_on_boundary':sum(distance(k)==0 for k in top),'top20_orientation':dict(Counter(decode(k)[2] for k in top)),'native_top20_prediction_ranks':[positions[k] for k in native_top],'spatial_centroid':[sum(decode(k)[axis]*v for k,v in density.items())/weights for axis in (0,1)],'spatial_density_sum':weights,'channel_net_touches':touches,'direction_touches':dict(directions),'span_touch_histogram':dict(sorted(spans.items())),'weighted_mean_R_ohm':r_weight/touches,'weighted_mean_C_farad':c_weight/touches}
 summaries[name]=summary;top_records[name]=[{'key':k,'density':density[k],'boundary_distance':distance(k),'native_density':spatial_maps['native'][k]} for k in top]
(out/'spatial_maps.json').write_text(json.dumps(spatial_maps,indent=2)+'\n');(out/'top20.json').write_text(json.dumps(top_records,indent=2)+'\n')
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'inputs_unchanged':True,'summaries':summaries,'outputs':{p.name:sha(p) for p in (out/'spatial_maps.json',out/'top20.json')}},indent=2)+'\n')
print(json.dumps(summaries,indent=2))
