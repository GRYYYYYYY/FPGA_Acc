"""Independent Fraction vectors/doubled-tie-ranks/exact topK and four-metric gates."""
import hashlib,json,math,sys
from fractions import Fraction
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_map_priority_trial_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def scores(resources,bins,ledger):
 channels={};acc=Counter();caps={tuple(b['key']):b['capacity'] for b in bins}
 for r in resources:
  n=r['id'];channels[n]=Fraction(ledger.get(n,0),r['capacity'])
  for k in r['bins']:acc[tuple(k)]+=ledger.get(n,0)
 return {'resource':channels,'spatial':{k:Fraction(acc[k],cap) for k,cap in caps.items()}}
def ranks(values):
 order=sorted(values,key=lambda k:(values[k],k));out={};i=0
 while i<len(order):
  j=i+1
  while j<len(order) and values[order[j]]==values[order[i]]:j+=1
  for k in order[i:j]:out[k]=i+1+j
  i=j
 return out
def rho(a,b):
 x,y=ranks(a),ranks(b);ids=sorted(x);assert set(x)==set(y);n=len(ids);sx=sum(x.values());sy=sum(y.values());vx=n*sum(v*v for v in x.values())-sx*sx;vy=n*sum(v*v for v in y.values())-sy*sy
 return None if not vx or not vy else (n*sum(x[k]*y[k] for k in ids)-sx*sy)/math.sqrt(vx*vy)
def main():
 case=sys.argv[1];source=D/case/'verification.json';workflow=read(source);target=R/'experiments/wbuart_map_priority_completed_metrics_v1_2026-10-20'/case;target.mkdir(parents=True,exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),source]};rows=[];vectors=0
 for item in workflow['comparisons']:
  sp=Path(item['specification']);s=read(sp);result=read(Path(item['comparison']))
  for n,h in result['bindings'].items():assert sha(Path(n))==h
  domain=read(Path(s['domain_proof']));folder=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');truth=read(Path(s['label_physical_audit']));tv=scores(resources,bins,{int(n):v for n,v in truth['node_occupancy'].items()});pred={'previous_native':s['source_frame'],**{n:a['frame'] for n,a in s['predictions'].items()}};metrics={}
  for name,path in pred.items():
   frame=read(Path(path));pv=scores(resources,bins,{int(n):v for n,v in frame['ledger'].items()});metrics[name]={};vectors+=1
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    pr=sorted(pv[scope],key=lambda i:(-pv[scope][i],i))[:k];tr=sorted(tv[scope],key=lambda i:(-tv[scope][i],i))[:k];hits=len(set(pr)&set(tr));value=rho(pv[scope],tv[scope]);got=result['metrics'][name][scope];assert got['top_k_hits']==hits and got['k']==k and got['universe_size']==len(pv[scope]);assert (value is None and got['spearman'] is None) or value is not None and abs(value-got['spearman'])<=1e-12;assert abs(got['precision_at_k']-hits/k)<1e-15
    assert got['prediction_top_k']==[list(x) if isinstance(x,tuple) else x for x in pr] and got['truth_top_k']==[list(x) if isinstance(x,tuple) else x for x in tr];metrics[name][scope]={'rho':value,'hits':hits}
  checks={}
  for control in ['previous_native','raw_min_on']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=metrics['native_retained_on'][scope],metrics[control][scope];defined=a['rho'] is not None and b['rho'] is not None;nonreg.extend([defined and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([defined and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   passed=all(nonreg) and any(strict);assert passed==result['checks'][control]['pass_primary_gate'];checks[control]=passed
  assert result['pass_case_gate']==all(checks.values());rows.append({'case':item['case'],'timing_policy':item['timing_policy'],'pass_case_gate':result['pass_case_gate'],'checks':checks,'metrics':metrics});bindings[str(sp)]=sha(sp);bindings[item['comparison']]=sha(Path(item['comparison']));print('PRIMARY_METRIC_RECHECK',item['case'],result['pass_case_gate'],flush=True)
 assert vectors==6 and len(rows)==2
 (target/'verification.json').write_text(json.dumps({'status':'ALL6_COMPLETED_CASE_VECTORS_AND2_ORIGINAL_GATES_INDEPENDENTLY_VERIFIED','rows':rows,'metric_vectors':vectors,'passed_case_gates':sum(r['pass_case_gate'] for r in rows),'strict_unseen_admitted':False,'quality_gate_changed':False,'bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
