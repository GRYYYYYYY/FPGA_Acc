"""Independent signed-delta/rational-rank/full-RR projection audit."""
import json,math,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_native_seeded_update_delta_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==3 and all(sha(root/'tools'/n)==h for n,h in p['metric_sources_sha256'].items())
def ranks(a):
 order=sorted(range(len(a)),key=lambda i:a[i]);result=[Fraction(0)]*len(a);i=0
 while i<len(order):
  j=i+1
  while j<len(order) and a[order[j]]==a[order[i]]:j+=1
  for k in order[i:j]:result[k]=Fraction(i+j-1,2)
  i=j
 return result
def check_rho(a,b,rho):
 a=ranks(a);b=ranks(b);mean=Fraction(len(a)-1,2);va=sum((x-mean)**2 for x in a);vb=sum((x-mean)**2 for x in b);expected=None if not va or not vb else float(sum((x-mean)*(y-mean) for x,y in zip(a,b)))/math.sqrt(float(va*vb));assert (expected is None and rho is None) or math.isclose(expected,rho,rel_tol=1e-12,abs_tol=1e-12)
def check_support(a,b,q):
 hit=len(a&b);assert q['predicted']==len(a) and q['native']==len(b) and q['intersection']==hit
 for key,denom in [('precision',len(a)),('recall',len(b)),('jaccard',len(a|b))]:assert q[key]==(hit/denom if denom else None)
rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert c['width']==row['width'] and all(sha(path)==h for path,h in c['bindings'].items());file=out/f"gf2_d{row['width']}_vectors.json";assert sha(file)==row['vector_sha256'];vectors=json.loads(file.read_text());old=json.loads(Path(c['old_prediction']).read_text());new=json.loads(Path(c['new_prediction']).read_text());po={int(n):v for n,v in old['ledger'].items()};pn={int(n):v for n,v in new['ledger'].items()};ao=audit(c['graph'],c['old_native_route']);an=audit(c['graph'],c['new_native_route']);to={int(n):v for n,v in ao['node_occupancy'].items()};tn={int(n):v for n,v in an['node_occupancy'].items()};assert not ao['overflow_units'] and not an['overflow_units'] and len(ao['connections'])==len(an['connections'])==row['connections'];nodes={int(n.get('id')):n for n in ET.parse(c['graph']).getroot().find('rr_nodes') if n.get('type') in ('CHANX','CHANY') and int(n.get('capacity'))>0};assert len(nodes)==row['channel_universe'] and [x['node'] for x in vectors['channels']]==sorted(nodes);pv={};tv={};cap=defaultdict(int);pb=defaultdict(int);tb=defaultdict(int)
 for item in vectors['channels']:
  n=item['node'];node=nodes[n];capacity=int(node.get('capacity'));assert item=={'node':n,'capacity':capacity,'old_predicted':po.get(n,0),'new_predicted':pn.get(n,0),'old_native':to.get(n,0),'new_native':tn.get(n,0)};pd=pn.get(n,0)-po.get(n,0);td=tn.get(n,0)-to.get(n,0);pv[n]=Fraction(pd,capacity);tv[n]=Fraction(td,capacity);loc=node.find('loc').attrib;segment=node.find('segment');sid=-1 if segment is None else int(segment.get('segment_id'))
  for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
   for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
    k=(int(loc.get('layer','0')),x,y,node.get('type'),sid);cap[k]+=capacity;pb[k]+=pd;tb[k]+=td
 assert vectors['bins']==[{'key':list(k),'capacity':cap[k],'predicted_delta':pb[k],'native_delta':tb[k]} for k in sorted(cap)]
 check_support({n for n,v in pv.items() if v},{n for n,v in tv.items() if v},row['changed_support']);check_support({n for n,v in pv.items() if v>0},{n for n,v in tv.items() if v>0},row['added_support']);check_support({n for n,v in pv.items() if v<0},{n for n,v in tv.items() if v<0},row['removed_support']);ids=sorted(nodes);bins=sorted(cap);check_rho([pv[n] for n in ids],[tv[n] for n in ids],row['signed_resource_spearman']);check_rho([Fraction(pb[k],cap[k]) for k in bins],[Fraction(tb[k],cap[k]) for k in bins],row['signed_spatial_spearman']);assert math.isclose(float(sum(abs(pv[n]-tv[n]) for n in ids)/len(ids)),row['signed_resource_MAE'],abs_tol=1e-12);assert math.isclose(float(sum(Fraction(abs(pb[k]-tb[k]),cap[k]) for k in bins)/len(bins)),row['signed_spatial_MAE'],abs_tol=1e-12)
 rows.append({'width':row['width'],'all_channel_delta_vectors_verified':len(ids),'changed_precision':row['changed_support']['precision'],'changed_recall':row['changed_support']['recall'],'signed_resource_spearman':row['signed_resource_spearman'],'signed_spatial_spearman':row['signed_spatial_spearman']})
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'OriginalXML universe/old-new native occupancies, estimator deltas, support/direction sets and Fraction-midrank metrics independently checked. Full cold reroute target, not native incremental routing or quality/publication/gain proof.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
