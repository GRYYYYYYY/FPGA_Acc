"""Frozen fold training and predictions; evaluation labels are not loaded."""
import json,math,time,sys
from array import array
from pathlib import Path
from compiled_logistic_batch_v1 import matrix,train
from forecast_split_provenance_v1 import check
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def main():
 manifest=Path(sys.argv[1]);m=read(manifest);episode=sys.argv[2];D=Path(m['output'])/episode;D.mkdir(exist_ok=False);spec=read(m['design']);source=read(m['features']);rows=source['rows'];inventory=read(m['inventory'])['rows'];training=[r for r in rows if not r['case'].endswith(episode)];testing=[r for r in rows if r['case'].endswith(episode)];assert len(training)==6 and len(testing)==3;raw={};labels={};bindings={str(manifest):sha(manifest)}
 for r in rows:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());assert len(a)==r['rows']*26 and all(map(math.isfinite,a));raw[r['case']]=a
 for r in training:
  reference=next(x for x in inventory if x['case']==r['case']);p=Path(reference['truth_payload']);occupancy={int(n):c for n,c in read(p)['node_occupancy'].items()};labels[r['case']]=[occupancy.get(n,0) for n in read(r['resource_ids'])];assert all(v in [0,1] for v in labels[r['case']]);bindings[str(p)]=sha(p)
 provenance={'samples':[],'model_fit_samples':[r['case'] for r in training],'feature_normalizer_fit_samples':[r['case'] for r in training],'label_transform_fit_samples':[],'feature_dependencies':[],'input_policy':'placement_and_prior_route','claim_strict_unseen_family':False}
 for r in rows:
  reference=next(x for x in inventory if x['case']==r['case']);ep=read(reference['endpoint']);provenance['samples'].append({'sample_id':r['case'],'family_id':'exposed_WBUART','source_sha256':ep['inputs']['net']['sha256'],'identity_kind':'packed_netlist_content_not_RTL_family_certificate','lineage_reviewed':False,'split':'train' if r in training else 'test'});provenance['feature_dependencies'].extend([{'sample_id':r['case'],'role':'rr_graph'},{'sample_id':r['case'],'role':'placement'},{'sample_id':r['case'],'role':'netlist'},{'sample_id':r['case'],'role':'prior_route','epoch_relation':'strictly_before_target'}])
 proof=check(provenance);(D/'fit_provenance.json').write_text(json.dumps({'declarations':provenance,'preflight':proof},indent=2)+'\n');outputs=[]
 for mode,d in [('main',26),('ablation',11)]:
  begin=time.perf_counter();X=[];Y=[]
  for r in training:
   a=raw[r['case']];X.extend([list(a[i*26:i*26+d]) for i in range(r['rows'])]);Y.extend(labels[r['case']])
  tick=time.perf_counter();n=len(X);mean=[math.fsum(x[j] for x in X)/n for j in range(d)];constant=[all(x[j]==X[0][j] for x in X) for j in range(d)];mean=[X[0][j] if constant[j] else mean[j] for j in range(d)];std=[1 if constant[j] else math.sqrt(math.fsum((x[j]-mean[j])**2 for x in X)/n) for j in range(d)];std=[s if s else 1 for s in std];X=[[(v-mean[j])/std[j] for j,v in enumerate(x)] for x in X];normalization_seconds=time.perf_counter()-tick;tick=time.perf_counter();answer=train(matrix(X,Y),spec['trainer']['iterations'],.001);training_seconds=time.perf_counter()-tick;model={'mode':mode,'columns':source['columns'][:d],'mean':mean,'std':std,'training_cases':[r['case'] for r in training],'test_cases':[r['case'] for r in testing],'normalization_seconds':normalization_seconds,'training_seconds':training_seconds,'setup_to_model_seconds':time.perf_counter()-begin,**answer};out=D/mode;out.mkdir();p=out/'model.json';p.write_text(json.dumps(model,indent=2)+'\n');bindings[str(p)]=sha(p)
  for r in testing:
   tick=time.perf_counter();a=raw[r['case']];pred=[]
   for i in range(r['rows']):
    z=answer['weights'][0]+sum(answer['weights'][j+1]*(a[i*26+j]-mean[j])/std[j] for j in range(d));value=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z));assert math.isfinite(value) and 0<=value<=1;pred.append(value)
   prediction_seconds=time.perf_counter()-tick;p=out/(r['case'].replace('/','_')+'_probabilities.json');p.write_text(json.dumps(pred,separators=(',',':'))+'\n');bindings[str(p)]=sha(p);outputs.append({'case':r['case'],'mode':mode,'model':str(out/'model.json'),'probabilities':str(p),'resource_ids':r['resource_ids'],'prediction_seconds':prediction_seconds})
  print('FOLD_MODEL_FROZEN',episode,mode,answer['initial_loss'],answer['final_loss'],answer['gradient_l2'],training_seconds,flush=True)
 bindings[str(D/'fit_provenance.json')]=sha(D/'fit_provenance.json');(D/'verification.json').write_text(json.dumps({'status':'FOLD_MODELS_AND6_PREDICTIONS_FROZEN','rows':outputs,'test_labels_loaded':False,'bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
