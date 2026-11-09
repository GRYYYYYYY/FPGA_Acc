"""Independent rational-rank and occupancy projection verification."""
import json,math,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_recurrence_resource_prediction_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==len(p['cases'])==3
assert all(sha(root/'tools'/name)==h for name,h in p['sources_sha256'].items())
def oracle_rank(values):
 order=sorted(range(len(values)),key=lambda i:values[i]);rank=[Fraction(0)]*len(values);pos=0
 while pos<len(order):
  end=pos+1
  while end<len(order) and values[order[end]]==values[order[pos]]:end+=1
  for i in order[pos:end]:rank[i]=Fraction(pos+end-1,2)
  pos=end
 return rank
def verify_metrics(pred,truth,k,reported):
 keys=sorted(pred);assert set(keys)==set(truth);a=oracle_rank([pred[n] for n in keys]);b=oracle_rank([truth[n] for n in keys]);mean=Fraction(len(keys)-1,2);cross=sum((u-mean)*(v-mean) for u,v in zip(a,b));va=sum((u-mean)**2 for u in a);vb=sum((u-mean)**2 for u in b);rho=None if not va or not vb else float(cross)/math.sqrt(float(va*vb));assert (rho is None and reported['spearman'] is None) or math.isclose(rho,reported['spearman'],rel_tol=1e-12,abs_tol=1e-12)
 k=min(k,len(keys));ap=sorted(keys,key=lambda n:(-pred[n],n))[:k];bt=sorted(keys,key=lambda n:(-truth[n],n))[:k];overlap=len(set(ap)&set(bt));assert reported['k']==k and reported['precision_at_k']==reported['recall_at_k']==overlap/k
 assert math.isclose(float(sum(abs(pred[n]-truth[n]) for n in keys)/len(keys)),reported['mae'],rel_tol=1e-12,abs_tol=1e-12)
 return {'native_boundary_tie_count':sum(truth[n]==truth[bt[-1]] for n in keys),'predicted_boundary_tie_count':sum(pred[n]==pred[ap[-1]] for n in keys),'native_strictly_above_boundary':sum(truth[n]>truth[bt[-1]] for n in keys),'predicted_strictly_above_boundary':sum(pred[n]>pred[ap[-1]] for n in keys)}
rows=[]
for case,row in zip(p['cases'],r['rows']):
 assert row['width']==case['width'] and sha(case['candidate'])==case['candidate_sha256'] and sha(case['native_route'])==case['native_route_sha256'] and sha(case['graph'])==case['graph_sha256'];file=out/f"gf2_d{row['width']}_vectors.json";assert sha(file)==row['vector_sha256'];vectors=json.loads(file.read_text());candidate=json.loads(Path(case['candidate']).read_text());pred={int(n):c for n,c in candidate['ledger'].items()};native=audit(case['graph'],case['native_route']);truth={int(n):c for n,c in native['node_occupancy'].items()};assert not native['overflow_units'] and len(native['connections'])==row['connections']
 nodes={int(n.get('id')):n for n in ET.parse(case['graph']).getroot().find('rr_nodes') if n.get('type') in ('CHANX','CHANY') and int(n.get('capacity'))>0};assert [v['node'] for v in vectors['channels']]==sorted(nodes);pv={};tv={};cp=defaultdict(int);pd=defaultdict(int);td=defaultdict(int)
 for item in vectors['channels']:
  n=item['node'];node=nodes[n];capacity=int(node.get('capacity'));assert item['capacity']==capacity and item['predicted']==pred.get(n,0) and item['native']==truth.get(n,0);pv[n]=Fraction(item['predicted'],capacity);tv[n]=Fraction(item['native'],capacity);loc=node.find('loc').attrib;segment=node.find('segment');sid=-1 if segment is None else int(segment.get('segment_id'))
  for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
   for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
    key=(int(loc.get('layer','0')),x,y,node.get('type'),sid);cp[key]+=capacity;pd[key]+=item['predicted'];td[key]+=item['native']
 assert vectors['bins']==[{'key':list(k),'capacity':cp[k],'predicted':pd[k],'native':td[k]} for k in sorted(cp)]
 a={n for n,v in pv.items() if v>0};b={n for n,v in tv.items() if v>0};intersection=len(a&b);support=row['support'];assert support['predicted_positive']==len(a) and support['native_positive']==len(b) and support['intersection']==intersection and support['precision']==intersection/len(a) and support['recall']==intersection/len(b) and support['jaccard']==intersection/len(a|b)
 concrete_ties=verify_metrics(pv,tv,max(1,len(nodes)//20),row['concrete']);spatial_ties=verify_metrics({k:Fraction(pd[k],v) for k,v in cp.items()},{k:Fraction(td[k],v) for k,v in cp.items()},20,row['spatial'])
 assert row['predicted_channel_union_demand']==sum(pred.get(n,0) for n in nodes) and row['native_channel_union_demand']==sum(truth.get(n,0) for n in nodes)
 rows.append({'width':row['width'],'full_channel_universe_verified':len(nodes),'support_precision':support['precision'],'support_recall':support['recall'],'resource_spearman':row['concrete']['spearman'],'spatial_spearman':row['spatial']['spearman'],'concrete_topset_ties':concrete_ties,'spatial_topset_ties':spatial_ties,'all_channel_utilizations_binary':all(v in (0,1) for v in (*pv.values(),*tv.values()))})
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'Independent XML universe/occupancy/spatial reconstruction and Fraction midrank correlation/support/topset/MAE checks. Tie counts interpret fixed scores; not posthoc model tuning. All siblings form one family, no independent-sample statistical gain claim.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
