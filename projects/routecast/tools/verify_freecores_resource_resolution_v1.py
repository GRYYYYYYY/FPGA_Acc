"""Independent rational pooling, conservation and histogram metric proof."""
import sys,json,math,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/freecores_resource_resolution_v1_2026-10-08';rp=D/'comparison.json';r=json.loads(rp.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings={**r['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(Path(__file__))};p=json.loads((D/'protocol.json').read_text());assert [x['name'] for x in r['rows']]==p['cases']==['8051','xtea'];methods=p['axis_indices'];checked=0
for row in r['rows']:
 name=row['name'];data=json.loads((D/name/'vectors.json').read_text());vec={tuple(x['key']):x for x in data};assert len(vec)==len(data)==row['fine_bins'];assert all(x['capacity']>0 and set(x['predictions'])==set(methods) for x in data)
 # Original XML capacities/features plus bound raw demand and native ledger.
 graph=R/'experiments/freecores_rr_only_v1_2026-10-08'/name/'rr_graph.xml';pred=json.loads((R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident/sketch.json').read_text())['ledger'];native=json.loads((R/'experiments/freecores_native_cold_v1_2026-10-08'/name/'physical_audit.json').read_text())['node_occupancy'];physical=defaultdict(lambda:[0,0,0]);stack=[]
 for event,el in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(el);continue
  if el.tag=='node' and el.get('type') in ['CHANX','CHANY'] and int(el.get('capacity'))>0:
   loc=el.find('loc');seg=el.find('segment');nid=el.get('id')
   for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
     key=(int(loc.get('layer','0')),x,y,el.get('type'),int(seg.get('segment_id')) if seg is not None else -1,el.get('direction','NONE'));record=physical[key];record[0]+=int(el.get('capacity'));record[1]+=pred.get(nid,0);record[2]+=native.get(nid,0)
  if el.tag in ['node','edge']:
   if len(stack)>1:stack[-2].remove(el)
   el.clear()
  stack.pop()
 assert set(physical)==set(vec) and all(physical[k]==[x['capacity'],x['predicted_count'],x['native_count']] for k,x in vec.items());truth={k:Fraction(x['native_count'],x['capacity']) for k,x in vec.items()}
 for method,axes in methods.items():
  groups=defaultdict(list)
  for key in vec:groups[tuple(key[i] for i in axes)].append(key)
  assert len(groups)==row['projection_groups'][method];values={k:Fraction(*x['predictions'][method]) for k,x in vec.items()}
  for group,keys in groups.items():
   numerator=sum(vec[k]['predicted_count'] for k in keys);denominator=sum(vec[k]['capacity'] for k in keys);value=Fraction(numerator,denominator);assert all(values[k]==value for k in keys);assert sum(values[k]*vec[k]['capacity'] for k in keys)==numerator
  def ranks(values):
   hist=Counter(values.values());prior=0;table={}
   for value,n in sorted(hist.items()):table[value]=prior+(n-1)/2;prior+=n
   return {k:table[v] for k,v in values.items()}
  a,b=ranks(values),ranks(truth);mean=(len(vec)-1)/2;cov=sum((a[k]-mean)*(b[k]-mean) for k in vec);den=math.sqrt(sum((a[k]-mean)**2 for k in vec)*sum((b[k]-mean)**2 for k in vec));rho=None if den==0 else cov/den;m=row['metrics'][method]
  if rho is None:assert m['spearman'] is None
  else:assert abs(rho-m['spearman'])<1e-12
  k=min(20,len(vec));pt=sorted(vec,key=lambda n:(-values[n],n))[:k];tt=sorted(vec,key=lambda n:(-truth[n],n))[:k];hit=len(set(pt)&set(tt))/k;assert m['precision_at_k']==m['recall_at_k']==hit and m['k']==k and m['universe_size']==len(vec);mae=sum(abs(values[n]-truth[n]) for n in vec)/len(vec);assert abs(float(mae)-m['mae'])<1e-12;assert abs(float(truth[tt[-1]])-m['truth_k_boundary'])<1e-12 and abs(float(values[pt[-1]])-m['prediction_k_boundary'])<1e-12;assert m['nonzero_truth']==sum(v>0 for v in truth.values());checked+=1
assert checked==10 and all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,all_original_XML_fine_bins_ledgers_rational_pooling_and_conservation_pass=True,all_10_complete_metric_vectors_histogram_verified=True,metric_vectors=checked,scope='Independent original XML fine-bin reconstruction, exact rational pooling/mass conservation, average tie ranks/top20/MAE. Output resolution only; no graph direction removal, physical routing/gain/unseen-family/HDL timing claim.'),indent=2)+'\n');print('PASS original XML, exact conserved resolution projections and 10 metric vectors',flush=True)
