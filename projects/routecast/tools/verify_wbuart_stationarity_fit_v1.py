"""Independent train classification by logit sign and ROC by rank sum."""
import json,math
from pathlib import Path
from array import array
from prediction_metrics import ranks
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_logistic_stationarity_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'train_fit_comparison_v1.json';v=read(p);assert all(sha(name)==h for name,h in v['bindings'].items());features=read(E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json')['rows'];inventory=read(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json')['rows'];raw={};labels={}
 for r in features:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());raw[r['case']]=[list(a[i*26:(i+1)*26]) for i in range(r['rows'])];target=read(next(x['truth_payload'] for x in inventory if x['case']==r['case']));occupancy={int(n):c for n,c in target['node_occupancy'].items()};labels[r['case']]=[occupancy.get(n,0) for n in read(r['resource_ids'])]
 checked=[]
 for row in v['rows']:
  m=read(row['model']);old=read(m['original_model']);values=[];ys=[];errors=0;old_errors=0;gap=[]
  for case in m['training_cases']:
   for x,y in zip(raw[case],labels[case]):
    z=m['weights'][0]+sum(w*(a-b)/s for w,a,b,s in zip(m['weights'][1:],x,m['mean'],m['std']));z0=old['weights'][0]+sum(w*(a-b)/s for w,a,b,s in zip(old['weights'][1:],x,old['mean'],old['std']));errors+=int(int(z>=0)!=y);old_errors+=int(int(z0>=0)!=y);values.append(z);ys.append(y);gap.append(min(abs(z),abs(z0)))
  assert min(gap)>1e-12 and errors==row['Newton_half_train_errors'] and old_errors==row['GD1000_half_train_errors'];rs=ranks(values);positive=sum(ys);auc=(sum(r+1 for r,y in zip(rs,ys) if y)-positive*(positive+1)/2)/(positive*(len(ys)-positive));assert abs(auc-row['Newton_train_ROC_AUC'])<=1e-12;checked.append({'episode':row['episode'],'mode':row['mode'],'new_errors':errors,'old_errors':old_errors,'minimum_logit_decision_margin':min(gap)})
 out=D/'independent_train_fit_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL6_TRAIN_ERROR_AND_ROC_COMPARISONS_VERIFIED','rows':checked,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py')},'scope':'Fixed train data, no new fits; numerical model gradients/objectives qualified separately.'},indent=2)+'\n');print('STATIONARITY_TRAIN_FIT_VERIFIED')
if __name__=='__main__':main()
