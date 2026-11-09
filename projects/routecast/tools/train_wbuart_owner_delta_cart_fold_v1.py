"""One new38-column owner-context tree per fold; old31 control unchanged."""
import json,time,sys
from pathlib import Path
from array import array
from compiled_fixed_cart_v1 import train,matrix,probability
from forecast_split_provenance_v1 import check
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def main():
 mp=Path(sys.argv[1]);m=read(mp);episode=sys.argv[2];D=Path(m['output'])/episode;D.mkdir(exist_ok=False);features=read(m['features'])['rows'];inventory=read(m['inventory'])['rows'];original=Path(m['original'])/episode;raw={};bindings={str(mp):sha(mp)};outputs=[];provenance=read(original/'fit_provenance.json')['declarations'];provenance['feature_normalizer_fit_samples']=[];(D/'fit_provenance.json').write_text(json.dumps({'declarations':provenance,'preflight':check(provenance)},indent=2)+'\n')
 for r in features:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());raw[r['case']]=[list(a[i*38:(i+1)*38]) for i in range(r['rows'])]
 for mode,d in [('main',38)]:
  previous_path=original/mode/'model.json';previous=read(previous_path);training=previous['training_cases'];testing=previous['test_cases'];X=[];Y=[]
  for case in training:
   X.extend(row[:d] for row in raw[case]);r=next(q for q in features if q['case']==case);target_path=Path(next(q['truth_payload'] for q in inventory if q['case']==case));target={int(n):c for n,c in read(target_path)['node_occupancy'].items()};Y.extend(target.get(n,0) for n in read(r['resource_ids']));bindings[str(target_path)]=sha(target_path)
  tick=time.perf_counter();model=train(matrix(X,Y),depth=8,minleaf=64);seconds=time.perf_counter()-tick;out=D/mode;out.mkdir();model.update(mode=mode,columns=read(m['features'])['columns'],training_cases=training,test_cases=testing,transform_policy='Raw original columns; no fitted transform',training_seconds=seconds,original_model=str(previous_path));p=out/'model.json';p.write_text(json.dumps(model,indent=2)+'\n');bindings[str(p)]=sha(p);bindings[str(previous_path)]=sha(previous_path)
  for case in testing:
   tick=time.perf_counter();scores=[probability(row[:d],model) for row in raw[case]];seconds=time.perf_counter()-tick;p=out/(case.replace('/','_')+'_probabilities.json');p.write_text(json.dumps(scores,separators=(',',':'))+'\n');r=next(q for q in features if q['case']==case);bindings[str(p)]=sha(p);outputs.append({'case':case,'mode':mode,'model':str(out/'model.json'),'probabilities':str(p),'resource_ids':r['resource_ids'],'prediction_seconds':seconds})
  print('CART_MODEL_FROZEN',episode,mode,len(model['nodes']),model['training_seconds'],flush=True)
 bindings[str(D/'fit_provenance.json')]=sha(D/'fit_provenance.json');(D/'verification.json').write_text(json.dumps({'status':'CART_FOLD_MODELS_AND_PREDICTIONS_FROZEN','rows':outputs,'test_labels_loaded':False,'bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
