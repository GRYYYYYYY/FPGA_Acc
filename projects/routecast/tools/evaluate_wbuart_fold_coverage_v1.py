"""Frozen-model train/test fit and exact-support strata; no new predictor fit."""
import json,math
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction as F
from evaluate_wbuart_half_decision_v1 import auc
from feature_alias_bounds_v1 import limits
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fold_coverage_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def prediction(row,model):
 z=model['weights'][0]+sum(w*(x-m)/s for w,x,m,s in zip(model['weights'][1:],row,model['mean'],model['std']));p=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z));return z,p
def metrics(values,ys,losses):
 return {'resources':len(ys),'binary_errors':sum(int(p>=.5)!=y for p,y in zip(values,ys)),'error_fraction':sum(int(p>=.5)!=y for p,y in zip(values,ys))/len(ys),'ROC_AUC':auc(values,ys),'BCE':math.fsum(losses)/len(losses)}
def main():
 source=D/'coverage_frozen.json';v=read(source);assert len(v['rows'])==18 and not v['target_labels_read'];assert all(sha(p)==h for p,h in v['bindings'].items());features_path=E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json';features=read(features_path)['rows'];workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];raw={};labels={};ids={};bindings={str(p):sha(p) for p in [source,Path(__file__),features_path,R/'tools/evaluate_wbuart_half_decision_v1.py',R/'tools/feature_alias_bounds_v1.py']}
 for r in features:
  case=r['case'];a=array('d');a.frombytes(Path(r['matrix']).read_bytes());raw[case]=[tuple(a[i*26:(i+1)*26]) for i in range(r['rows'])];ids[case]=read(r['resource_ids']);sp=next(x['specification'] for x in workflow if x['case']==case);s=read(sp);p=s['label_physical_audit'];target={int(n):c for n,c in read(p)['node_occupancy'].items()};labels[case]=[target.get(n,0) for n in ids[case]];assert set(labels[case])=={0,1};bindings[p]=sha(p)
 outputs=[];model_cache={}
 for r in v['rows']:
  model_path=r['model'];model=read(model_path);d=len(model['mean'])
  if model_path not in model_cache:
   index=defaultdict(lambda:[0,0]);ps=[];ys=[];losses=[]
   for case in model['training_cases']:
    for row,y in zip(raw[case],labels[case]):
     key=row[:d];index[key][0]+=1;index[key][1]+=y;z,p=prediction(key,model);ps.append(p);ys.append(y);losses.append(max(z,0)-y*z+math.log1p(math.exp(-abs(z))))
   fit=metrics(ps,ys,losses);bound=limits(index.values());assert abs(fit['BCE']+.001*sum(w*w for w in model['weights'][1:])/2-model['final_loss'])<=1e-10;fit['minimum_pooled_training_alias_errors']=bound['minimum_binary_errors'];fit['maximum_pooled_training_alias_ROC_AUC']=str(bound['maximum_ROC_AUC']);model_cache[model_path]=(index,fit)
  index,fit=model_cache[model_path];case=r['case'];ps=[];ys=labels[case];losses=[];strata={name:{'resources':0,'model_errors':0,'training_majority_diagnostic_errors':0,'training_majority_predictions':0,'seen_vectors_with_training_label_conflict':0} for name in r['counts']};coverage=read(r['coverage'])
  for row,y,cov in zip(raw[case],ys,coverage):
   key=row[:d];z,p=prediction(key,model);ps.append(p);losses.append(max(z,0)-y*z+math.log1p(math.exp(-abs(z))));stat=strata[cov['category']];stat['resources']+=1;stat['model_errors']+=int(int(p>=.5)!=y)
   if key in index:
    n,positive=index[key];stat['training_majority_predictions']+=1;stat['training_majority_diagnostic_errors']+=int(int(2*positive>=n)!=y);stat['seen_vectors_with_training_label_conflict']+=int(0<positive<n)
  result={'case':case,'mode':r['mode'],'model':model_path,'coverage':r['coverage'],'coverage_counts':r['counts'],'training_fit':fit,'test_fit':metrics(ps,ys,losses),'strata':strata};outputs.append(result);print('FOLD_COVERAGE_FIT',case,r['mode'],round(fit['error_fraction'],4),round(result['test_fit']['error_fraction'],4),flush=True)
 assert len(outputs)==18 and len(model_cache)==6
 out=D/'evaluation_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_FROZEN_MODEL_TRAIN_TEST_FITS_AND_COVERAGE_STRATA_EVALUATED','rows':outputs,'models':6,'bindings':bindings,'scope':'Retrospective exposed-family fit diagnostics. Exact unseen vector is not by itself OOD; train-range inclusion is not joint coverage. Shared-vector training majority is diagnostic only and abstains on uncovered rows; never substituted for full predictor gates.'},indent=2)+'\n')
if __name__=='__main__':main()
