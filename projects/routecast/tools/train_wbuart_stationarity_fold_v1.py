"""Same original data/transform/objective; train-only Newton stopping diagnostic."""
import json,math,time,sys
from array import array
from pathlib import Path
from compiled_logistic_batch_v1 import matrix
from compiled_logistic_newton_v1 import train
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def main():
 mp=Path(sys.argv[1]);m=read(mp);ep=sys.argv[2];D=Path(m['output'])/ep;D.mkdir(exist_ok=False);features=read(m['features'])['rows'];inventory=read(m['inventory'])['rows'];old=Path(m['original'])/ep;raw={};bindings={str(mp):sha(mp)};rows=[]
 for r in features:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());assert len(a)==r['rows']*26;raw[r['case']]=a
 provenance=old/'fit_provenance.json';(D/'fit_provenance.json').write_bytes(provenance.read_bytes());bindings[str(provenance)]=sha(provenance)
 for mode in ['main','ablation']:
  previous_path=old/mode/'model.json';previous=read(previous_path);training=previous['training_cases'];testing=previous['test_cases'];d=len(previous['mean']);means=previous['mean'];stds=previous['std'];X=[];Y=[]
  for case in training:
   r=next(x for x in features if x['case']==case);a=raw[case];X.extend([[(a[i*26+j]-means[j])/stds[j] for j in range(d)] for i in range(r['rows'])]);target_path=Path(next(x['truth_payload'] for x in inventory if x['case']==case));truth={int(n):c for n,c in read(target_path)['node_occupancy'].items()};Y.extend(truth.get(n,0) for n in read(r['resource_ids']));bindings[str(target_path)]=sha(target_path)
  tick=time.perf_counter();answer=train(matrix(X,Y));seconds=time.perf_counter()-tick;out=D/mode;out.mkdir();model={**answer,'mode':mode,'columns':previous['columns'],'mean':means,'std':stds,'training_cases':training,'test_cases':testing,'original_model':str(previous_path),'original_final_loss':previous['final_loss'],'training_seconds':seconds,'transform_policy':'Exact original train-only transform reused without refit'};p=out/'model.json';p.write_text(json.dumps(model,indent=2)+'\n');bindings[str(p)]=sha(p);bindings[str(previous_path)]=sha(previous_path)
  for case in testing:
   r=next(x for x in features if x['case']==case);a=raw[case];tick=time.perf_counter();scores=[]
   for i in range(r['rows']):
    z=answer['weights'][0]+sum(answer['weights'][j+1]*(a[i*26+j]-means[j])/stds[j] for j in range(d));scores.append(1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z)))
   seconds_predict=time.perf_counter()-tick;p=out/(case.replace('/','_')+'_probabilities.json');p.write_text(json.dumps(scores,separators=(',',':'))+'\n');bindings[str(p)]=sha(p);rows.append({'case':case,'mode':mode,'model':str(out/'model.json'),'probabilities':str(p),'resource_ids':r['resource_ids'],'prediction_seconds':seconds_predict,'numeric_stationarity':answer['status']=='NUMERIC_STATIONARITY'})
  print('NEWTON_MODEL_FROZEN',ep,mode,answer['status'],answer['iterations'],answer['final_loss'],answer['gradient_inf'],flush=True)
 bindings[str(D/'fit_provenance.json')]=sha(D/'fit_provenance.json');(D/'verification.json').write_text(json.dumps({'status':'SAME_OBJECTIVE_NEWTON_MODELS_AND_PREDICTIONS_FROZEN','rows':rows,'test_labels_loaded':False,'bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
