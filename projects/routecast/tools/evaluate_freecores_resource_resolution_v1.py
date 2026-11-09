"""Fixed demand-output resolution ablation, not graph/search semantics removal."""
import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
D=R/'experiments/freecores_resource_resolution_v1_2026-10-08';D.mkdir();bindings=closure([Path(__file__)]);cases=['8051','xtea'];axes={'full':(0,1,2,3,4,5),'no_polarity':(0,1,2,3,4),'no_segment':(0,1,2,3,5),'no_orientation':(0,1,2,4,5),'no_channel_labels':(0,1,2)}
for name in cases:
 proof=R/'experiments/freecores_hotspots_v1_2026-10-08'/name/'metric_verification.json';v=json.loads(proof.read_text());assert v['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and all(sha(k)==h for k,h in v['bindings'].items());bindings[str(proof)]=sha(proof)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,axis_indices=axes,fine_key=['layer','x','y','CHANX/CHANY','segment_id','direction'],rule='Capacity-weighted utilization pooling of predicted counts only, then reconstruct all original fine bins; native truth never pooled or used to choose groups. Fixed shared-span RC final demand and same original cold labels. Sum of predicted count conserved within every projection group, exact rational arithmetic. Evaluate all methods on identical full fine-bin universe, top20 and average tie ranks.',scope='Previously observed development output representation ablation; physical RR directed arcs/raw RC/trees remain unchanged. Removing direction/segment metadata labels alone is not a search ablation; this experiment does not prove graph-connectivity/RC segment semantic necessity or native speed.'),indent=2)+'\n');rows=[]
for name in cases:
 resident=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident';sp=resident/'sketch.json';c=json.loads(sp.read_text());np=R/'experiments/freecores_native_cold_v1_2026-10-08'/name/'physical_audit.json';native=json.loads(np.read_text());graph=R/'experiments/freecores_rr_only_v1_2026-10-08'/name/'rr_graph.xml';oldp=R/'experiments/freecores_hotspots_v1_2026-10-08'/name/'comparison_vectors.json';old=json.loads(oldp.read_text());bindings.update({str(p):sha(p) for p in [sp,np,graph,oldp]});caps=Counter();pred=Counter();truth=Counter();stack=[];inventory=Counter()
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='node' and el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
   n=el.get('id');cap=int(el.get('capacity'));loc=el.find('loc').attrib;s=el.find('segment');seg=int(s.get('segment_id')) if s is not None else -1;direction=el.get('direction','NONE');inventory[el.get('type'),seg,direction]+=1
   for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
     k=(int(loc.get('layer','0')),x,y,el.get('type'),seg,direction);caps[k]+=cap;pred[k]+=c['ledger'].get(n,0);truth[k]+=native['node_occupancy'].get(n,0)
  if el.tag in {'node','edge'}:
   if len(stack)>1:stack[-2].remove(el)
   el.clear()
  stack.pop()
 coarse_cap=Counter();coarse_p=Counter();coarse_t=Counter()
 for k,cap in caps.items():coarse_cap[k[:5]]+=cap;coarse_p[k[:5]]+=pred[k];coarse_t[k[:5]]+=truth[k]
 assert {tuple(x['key']):x['capacity'] for x in old['bins']}==dict(coarse_cap)
 assert all(coarse_p[tuple(x['key'])]==x['predictions']['wire_shared'] and coarse_t[tuple(x['key'])]==x['native'] for x in old['bins'])
 values={};group_sizes={}
 for method,indices in axes.items():
  gc=Counter();gp=Counter()
  for k,cap in caps.items():group=tuple(k[i] for i in indices);gc[group]+=cap;gp[group]+=pred[k]
  values[method]={k:Fraction(gp[tuple(k[i] for i in indices)],gc[tuple(k[i] for i in indices)]) for k in caps};mass=defaultdict(Fraction)
  for k,cap in caps.items():mass[tuple(k[i] for i in indices)]+=values[method][k]*cap
  assert all(mass[g]==gp[g] for g in gc);group_sizes[method]=len(gc)
 native_values={k:Fraction(truth[k],cap) for k,cap in caps.items()};metrics={}
 for method,val in values.items():
  m=compare(val,native_values,20)
  for k in ['mae','truth_k_boundary','prediction_k_boundary']:m[k]=float(m[k])
  metrics[method]=m
 w=D/name;w.mkdir();vectors=[dict(key=list(k),capacity=caps[k],native_count=truth[k],predicted_count=pred[k],predictions={m:[values[m][k].numerator,values[m][k].denominator] for m in axes}) for k in sorted(caps)];vp=w/'vectors.json';vp.write_text(json.dumps(vectors)+'\n');bindings[str(vp)]=sha(vp);rows.append(dict(name=name,fine_bins=len(caps),projection_groups=group_sizes,channel_inventory=[dict(type=k[0],segment=k[1],direction=k[2],nodes=n) for k,n in sorted(inventory.items())],metrics=metrics));print(name,{m:(v['spearman'],v['precision_at_k'],v['mae']) for m,v in metrics.items()},flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'comparison.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Fixed complete fine-bin output resolution comparison; native truth unchanged, not routing-search or legality ablation, not strict heldout/HDL/timing/netgain proof.'),indent=2)+'\n')
