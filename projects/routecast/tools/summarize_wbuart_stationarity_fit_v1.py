"""Frozen train-only error/ROC change after same-objective solver convergence."""
import json,math
from pathlib import Path
from array import array
from evaluate_wbuart_half_decision_v1 import auc
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_logistic_stationarity_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=D/'independent_verification_v1.json';assert all(sha(p)==h for p,h in read(proof)['bindings'].items());features=read(E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json')['rows'];inventory=read(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json')['rows'];oldfits=read(E/'wbuart_fold_coverage_v1_2026-10-20/evaluation_v1.json')['rows'];raw={};rows=[];bindings={str(proof):sha(proof),str(Path(__file__)):sha(__file__)}
 for r in features:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());raw[r['case']]=[list(a[i*26:(i+1)*26]) for i in range(r['rows'])]
 for ep in ['episode_01','episode_02','episode_03']:
  for mode in ['main','ablation']:
   p=D/ep/mode/'model.json';m=read(p);scores=[];ys=[]
   for case in m['training_cases']:
    r=next(q for q in features if q['case']==case);target_path=Path(next(q['truth_payload'] for q in inventory if q['case']==case));target={int(n):c for n,c in read(target_path)['node_occupancy'].items()};y=[target.get(n,0) for n in read(r['resource_ids'])];ys.extend(y)
    for row in raw[case]:
     z=m['weights'][0]+sum(w*(x-mean)/std for w,x,mean,std in zip(m['weights'][1:],row,m['mean'],m['std']));scores.append(1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z)))
    bindings[str(target_path)]=sha(target_path)
   old=next(q['training_fit'] for q in oldfits if q['model']==m['original_model']);errors=sum(int(p>=.5)!=y for p,y in zip(scores,ys));rows.append({'episode':ep,'mode':mode,'model':str(p),'numeric_status':m['status'],'gradient_inf':m['gradient_inf'],'Newton_train_loss':m['final_loss'],'GD1000_train_loss':m['original_final_loss'],'Newton_half_train_errors':errors,'GD1000_half_train_errors':old['binary_errors'],'training_resources':len(ys),'training_alias_minimum_errors':old['minimum_pooled_training_alias_errors'],'Newton_train_ROC_AUC':auc(scores,ys),'GD1000_train_ROC_AUC':old['ROC_AUC']});bindings[str(p)]=sha(p);print('STATIONARY_FIT',ep,mode,old['binary_errors'],errors,flush=True)
 assert len(rows)==6
 out=D/'train_fit_comparison_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL6_SAME_OBJECTIVE_TRAIN_FITS_COMPARED','rows':rows,'bindings':bindings,'scope':'Training diagnosis only; same transform/data/objective, no classifier family change. Gradient stationarity is not exact proof; arbitrary-label alias lookup is not learned performance.'},indent=2)+'\n')
if __name__=='__main__':main()
