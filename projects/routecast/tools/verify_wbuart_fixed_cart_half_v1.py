"""Independent point thresholds, rank implementation, ROC and counterexamples."""
import json,math,random
from pathlib import Path
from fractions import Fraction as F
from prediction_metrics import compare,ranks
from verify_wbuart_best_support_ranking_v1 import normalize
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_cart_half_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'evaluation_v1.json';v=read(p);assert all(sha(path)==h for path,h in v['bindings'].items());predictions=read(D/'predictions_frozen.json')['rows'];workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];vectors=0;checked=[]
 for row in v['rows']:
  r=next(x for x in predictions if x['case']==row['case'] and x['mode']==row['mode']);s=read(next(x['specification'] for x in workflow if x['case']==row['case']));domain=read(s['domain_proof']);directory=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (directory/'resources.jsonl').read_text().splitlines()];bins=read(directory/'spatial_bins.json');ids=read(r['resource_ids']);soft=read(r['probabilities']);point=read(r['point_counts']);assert point==[1 if value>=1/2 else 0 for value in soft];labels={int(n):c for n,c in read(s['label_physical_audit'])['node_occupancy'].items()};truth=normalize(resources,bins,labels);counts={'point':dict(zip(ids,point)),'soft':{n:F.from_float(x) for n,x in zip(ids,soft)},'previous_native':{int(n):c for n,c in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(n):c for n,c in read(s['predictions']['raw_min_on']['frame'])['ledger'].items()}}
  for name,values in counts.items():
   normalized=normalize(resources,bins,values);vectors+=1
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    metric=compare(normalized[scope],truth[scope],k);got=row['metrics'][name][scope];assert got['hits']==round(k*metric['precision_at_k']) and got['k']==k;assert (metric['spearman'] is None and got['rho'] is None) or metric['spearman'] is not None and abs(metric['spearman']-got['rho'])<=1e-12
  checks={}
  for control in ['previous_native','original_H0_raw_min_on']:
   weak=[];strong=[]
   for scope in ['resource','spatial']:
    a,b=row['metrics']['point'][scope],row['metrics'][control][scope];valid=a['rho'] is not None and b['rho'] is not None;weak.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strong.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   checks[control]=all(weak) and any(strong)
  assert checks==row['comparisons'] and all(checks.values())==row['both_original_comparisons'];ys=[labels.get(n,0) for n in ids];m=sum(ys);n=len(ids);ranking=ranks(soft);auc=(sum(rank+1 for rank,y in zip(ranking,ys) if y)-m*(m+1)/2)/(m*(n-m));assert abs(auc-row['soft_ROC_AUC'])<=1e-15
  predicted={i for i,p in enumerate(point) if p};actual={i for i,y in enumerate(ys) if y};assert row['point_confusion']=={'TP':len(predicted&actual),'FP':len(predicted-actual),'FN':len(actual-predicted),'TN':n-len(predicted|actual)}
  checked.append({'case':row['case'],'mode':row['mode'],'pass':all(checks.values())})
 assert len(checked)==18 and vectors==72
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_CART_HALF_DECISIONS_72_METRIC_VECTORS_AND_AUC_VERIFIED','rows':checked,'metric_vectors':vectors,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py'),str(R/'tools/verify_wbuart_best_support_ranking_v1.py'):sha(R/'tools/verify_wbuart_best_support_ranking_v1.py')},'scope':'Original metric semantics and supplemental fixed0.5 representation only.  preserve old results and thresholds.'},indent=2)+'\n');print('ALL_CART_HALF_DECISIONS_VERIFIED',vectors)
if __name__=='__main__':main()
