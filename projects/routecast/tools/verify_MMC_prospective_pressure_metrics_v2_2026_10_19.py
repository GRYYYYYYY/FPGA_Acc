"""Independent output check using histogram score groups and separate ranks."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
from prediction_metrics import spearman
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_prospective_pressure_evaluation_v2_2026-10-19';rp=O/'results.json'
 if not rp.exists():raise SystemExit('NOT_READY: prospective evaluation result required')
 result=json.loads(rp.read_text());assert result['status']=='all3_registered_pressure_forecasts_evaluated'
 for p,h in result['bindings'].items():assert sha(p)==h,p
 P=R/'experiments/mmc_prospective_pressure_protocol_v2_2026-10-19/protocol.json';spec=json.loads(P.read_text());cmd=spec['native_commands'][0]['argv'];graph=pathlib.Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(graph)==spec['bindings'][str(graph)];domain=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:domain.append(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 domain.sort();assert json.loads((O/'domain.json').read_text())==domain and len(domain)==258720;k=spec['top_k'];checks=0;decisions=[]
 for row in result['episodes']:
  name=row['episode'];pp=O/(name+'_predictions.json');assert result['bindings'][str(pp)]==sha(pp);pred=json.loads(pp.read_text());tp=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19'/name/'targets.json';assert result['bindings'][str(tp)]==sha(tp);targets=json.loads(tp.read_text());assert targets['first_target_iteration']==2
  for target,raw in targets['targets'].items():
   truth={int(n):x for n,x in raw.items()};t=[truth.get(n,0) for n in domain];total=sum(t)
   for model,s in pred.items():
    m=row['metrics'][target][model];assert len(s)==len(domain)
    if not total:assert m['status']=='unassessable' and m['capture'] is None;continue
    rho=spearman(s,t);assert m['spearman'] is None if rho is None else m['spearman'] is not None and abs(m['spearman']-rho)<1e-12
    counts=Counter(s);mass=Counter()
    for score,value in zip(s,t):mass[score]+=value
    left=k;captured=Fraction(0)
    for score,n in sorted(counts.items(),reverse=True):
     take=min(left,n);captured+=Fraction(take*mass[score],n);left-=take
     if not left:break
    assert Fraction(m['capture'])==captured/total
    selected=sorted(range(len(domain)),key=lambda i:(-s[i],domain[i]))[:k];assert Fraction(m['fixed_ID_capture'])==Fraction(sum(t[i] for i in selected),total);checks+=1
  primary=row['metrics']['sum_checkpoint_overflow_units'];c=primary['native_retained'];decision='pass'
  if c['capture'] is None or c['spearman'] is None:decision='unassessable'
  else:
   for model in ['raw_min','previous_native']:
    ref=primary[model]
    if ref['capture'] is None or ref['spearman'] is None:decision='unassessable';break
    x,y=Fraction(c['capture']),Fraction(ref['capture']);a,b=c['spearman'],ref['spearman']
    if x<y or a<b-1e-12 or (x==y and a<=b+1e-12):decision='fail';break
   if decision=='pass' and Fraction(c['capture'])<=Fraction(k,len(domain)):decision='fail'
  assert decision==row['primary_gate'];decisions.append(decision)
 assert result['all3_primary_gate_pass']==all(x=='pass' for x in decisions);assert len(decisions)==3
 proof=dict(status='all3_forecast_metrics_and_registered_decisions_independently_verified',bindings={str(rp):sha(rp),str(pathlib.Path(__file__).resolve()):sha(__file__),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py')},metric_vectors_checked=checks,decisions=decisions,all3_primary_gate_pass=result['all3_primary_gate_pass'],scope='Independent metric and decision audit only; no full-time gain or family-holdout claim.')
 with (O/'independent_metric_verification_v1.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(proof['status'],checks,decisions,flush=True)
if __name__=='__main__':main()
