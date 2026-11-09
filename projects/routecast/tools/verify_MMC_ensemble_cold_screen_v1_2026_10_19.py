"""Independent primary4metric verification of original cold necessary-control screen."""
import pathlib,json,hashlib,math,xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def rho(p,t):
 n=len(p);joint=Counter(zip(p,t));a=Counter(p);b=Counter(t)
 def ranks(c):
  offset=0;result={}
  for v,k in sorted(c.items()):result[v]=2*offset+k-1;offset+=k
  return result
 x,y=ranks(a),ranks(b);mean=n-1;cross=sum(k*(x[u]-mean)*(y[v]-mean) for (u,v),k in joint.items());xx=sum(k*(x[v]-mean)**2 for v,k in a.items());yy=sum(k*(y[v]-mean)**2 for v,k in b.items());return cross/math.sqrt(xx*yy) if xx and yy else None

def check(pred,truth,k,reported):
 ids=sorted(truth);a=[pred[n] for n in ids];b=[truth[n] for n in ids];r=rho(a,b);assert reported['spearman'] is None if r is None else reported['spearman'] is not None and abs(r-reported['spearman'])<1e-12
 selected_p=set(sorted(ids,key=lambda n:(-pred[n],n))[:k]);selected_t=set(sorted(ids,key=lambda n:(-truth[n],n))[:k]);precision=len(selected_p&selected_t)/k;assert precision==reported['precision_at_k'];assert reported['universe_size']==len(ids) and reported['k']==k;return r,precision

def main():
 O=R/'experiments/mmc_ensemble_cold_quality_screen_v1_2026-10-19';rp=O/'results.json'
 if not rp.exists():raise SystemExit('NOT_READY: cold screen results required')
 result=json.loads(rp.read_text())
 for p,h in result['bindings'].items():assert sha(p)==h,p
 graph=next(pathlib.Path(p) for p in result['bindings'] if p.endswith('rr_graph.xml'));nodes={};bins=Counter();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
    loc=e.find('loc');seg=e.find('segment');capacity=int(e.get('capacity'));keys=tuple((int(loc.get('layer','0')),x,y,e.get('type'),int(seg.get('segment_id')) if seg is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1));nodes[int(e.get('id'))]=(capacity,keys)
    for key in keys:bins[key]+=capacity
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(nodes)==258720 and len(bins)==17160;M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';sourceledger={int(n):Fraction(x) for n,x in json.loads(source.read_text())['ledger'].items()};decisions=[];vectors=0;bindings={str(rp):sha(rp),str(graph):sha(graph),str(source):sha(source),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for row in result['cases']:
  case=row['case'];cp=M/case/'expected_unique_NET_occupancy.json';tp=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case/'cold/physical_audit.json';candidate={int(n):Fraction(x) for n,x in json.loads(cp.read_text()).items()};truth={int(n):Fraction(x) for n,x in json.loads(tp.read_text())['node_occupancy'].items()};cv={m:{} for m in ['NET_tree_ensemble','previous_native']};tv={};bin_truth=Counter();bin_pred={m:Counter() for m in cv}
  for n,(capacity,keys) in nodes.items():
   tv[n]=truth.get(n,0)/capacity
   for m,ledger in [('NET_tree_ensemble',candidate),('previous_native',sourceledger)]:cv[m][n]=ledger.get(n,0)/capacity
   for key in keys:
    bin_truth[key]+=truth.get(n,0)
    for m,ledger in [('NET_tree_ensemble',candidate),('previous_native',sourceledger)]:bin_pred[m][key]+=ledger.get(n,0)
  bt={k:Fraction(bin_truth[k],capacity) for k,capacity in bins.items()};verified={}
  for model in cv:
   bp={k:Fraction(bin_pred[model][k],capacity) for k,capacity in bins.items()};verified[model]={}
   for scope,pred,t,k in [('concrete',cv[model],tv,12936),('spatial',bp,bt,20)]:verified[model][scope]=check(pred,t,k,row['metrics'][model][scope]);vectors+=1
  nonreg=[];strict=[]
  for scope in ['concrete','spatial']:
   for index in [0,1]:
    x=verified['NET_tree_ensemble'][scope][index];y=verified['previous_native'][scope][index];eps=1e-12 if index==0 else 0;nonreg.append(x is not None and y is not None and x>=y-eps);strict.append(x is not None and y is not None and x>y+eps)
  decision=all(nonreg) and any(strict);assert decision==row['previous_native_necessary_gate_pass'];decisions.append(decision);bindings[str(cp)]=sha(cp);bindings[str(tp)]=sha(tp);print('COLD FOURMETRIC VERIFIED',case,decision,flush=True)
 expected='UNRESOLVED_RAW_MIN_ON_CONTROL_MISSING' if all(decisions) else 'FAIL_NECESSARY_PREVIOUS_NATIVE_CONTROL';assert expected==result['status'] and not result['original_full_gate_pass'];proof=dict(status='ALL3_ORIGINAL_COLD_PRIMARY_METRIC_VECTORS_AND_NECESSARY_DECISIONS_VERIFIED',bindings=bindings,primary_metric_vectors_checked=vectors,case_necessary_gates=decisions,original_gate_status=expected,original_full_gate_pass=False,missing_raw_min_on_control=True,supplementary_off_control_metrics_independently_verified=False,scope='Independent XML domain, normalized values, histogram ranks and fixed-ID topK for candidate and previous_native only. All3case original gate fails if any necessary-control case fails. Passing never proves original full gate without raw_min_on. Separate temporal-pressure positive result unchanged; no unseen/speed claim.')
 with (O/'independent_primary_verification_v1.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
if __name__=='__main__':main()
