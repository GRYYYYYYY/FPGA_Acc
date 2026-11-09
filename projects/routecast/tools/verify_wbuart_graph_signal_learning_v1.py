"""Audit feature joins, fold provenance, train-only transforms, loss and predictions."""
import json,math
from pathlib import Path
from array import array
from collections import Counter
from exact_factor_elimination_v1 import sha
from forecast_split_provenance_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_graph_signal_learning_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def close(a,b,tol=1e-10):assert abs(a-b)<=tol*max(1,abs(a),abs(b)),(a,b)
def sigmoid(z):return 1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z))
def main():
 p=D/'predictions_frozen.json';v=read(p);m=read(D/'manifest.json');features=read(m['features']);inventory=read(m['inventory'])['rows'];signals=read(E/'wbuart_endpoint_graph_signals_v1_2026-10-20/verification.json');H=E/'wbuart_preroute_heterograph_v1_2026-10-20';raw={};graphs={};cells=0
 for doc in [v,m,features]:assert all(sha(path)==h for path,h in doc['bindings'].items())
 for r in features['rows']:
  signal=next(q for q in signals['rows'] if q['case']==r['case']);digest=signal['graph_sha256']
  if digest not in graphs:
   directory=H/'graphs'/digest;nodes={n['id']:n for n in lines(directory/'RR_nodes.jsonl')};incoming=Counter();outgoing=Counter()
   for e in lines(directory/'physical_edges.jsonl'):outgoing[e['source']]+=1;incoming[e['sink']]+=1
   graphs[digest]=(nodes,incoming,outgoing)
  nodes,incoming,outgoing=graphs[digest];messages={q['RR']:q['values'] for q in lines(signal['feature_file'])};prior={int(n):c for n,c in read(r['source_frame'])['ledger'].items()};a=array('d');a.frombytes(Path(r['matrix']).read_bytes());ids=read(r['resource_ids']);assert ids==sorted(q['id'] for q in lines(r['resources'])) and len(a)==26*len(ids)
  for i,n in enumerate(ids):
   rr=nodes[n];loc=rr['loc'];expected=[math.log1p(rr['capacity']),loc['xlow'],loc['xhigh'],loc['ylow'],loc['yhigh'],float(rr['type']=='CHANX'),float(rr['direction']=='INC_DIR'),float(rr['direction']=='DEC_DIR'),math.log1p(incoming[n]),math.log1p(outgoing[n]),math.log1p(prior.get(n,0))]+[math.log1p(x) for x in messages[n]]
   assert list(a[i*26:(i+1)*26])==expected;cells+=26
  raw[r['case']]=[list(a[i*26:(i+1)*26]) for i in range(len(ids))]
 models=0;probabilities=0
 for episode in ['episode_01','episode_02','episode_03']:
  fold=D/episode;proof=read(fold/'verification.json');assert not proof['test_labels_loaded'];assert all(sha(path)==h for path,h in proof['bindings'].items());declaration=read(fold/'fit_provenance.json');assert check(declaration['declarations'])==declaration['preflight'];training=sorted(case for case in raw if not case.endswith(episode));testing=sorted(case for case in raw if case.endswith(episode));assert declaration['declarations']['model_fit_samples']==training
  for case in testing:
   target=next(r['truth_payload'] for r in inventory if r['case']==case);assert target not in proof['bindings']
  Y=[]
  for case in training:
   reference=next(r for r in inventory if r['case']==case);target={int(n):c for n,c in read(reference['truth_payload'])['node_occupancy'].items()};ids=read(next(r['resource_ids'] for r in features['rows'] if r['case']==case));Y.extend(target.get(n,0) for n in ids)
  for mode,d in [('main',26),('ablation',11)]:
   model=read(fold/mode/'model.json');assert model['training_cases']==training and model['test_cases']==testing and model['iterations']==1000 and model['regularization']==.001 and model['step']==1/(d+1);X=[row[:d] for case in training for row in raw[case]];n=len(X);means=[];stds=[]
   for j in range(d):
    column=[x[j] for x in X];constant=min(column)==max(column);mean=column[0] if constant else math.fsum(column)/n;std=1 if constant else math.sqrt(math.fsum((x-mean)**2 for x in column)/n);std=std or 1;means.append(mean);stds.append(std);close(mean,model['mean'][j]);close(std,model['std'][j])
   w=model['weights'];assert len(w)==d+1 and all(map(math.isfinite,w));losses=[];gradient=[0.0]*(d+1)
   for x,y in zip(X,Y):
    x=[(a-b)/s for a,b,s in zip(x,means,stds)];z=w[0]+sum(a*b for a,b in zip(w[1:],x));residual=sigmoid(z)-y;losses.append(max(z,0)-y*z+math.log1p(math.exp(-abs(z))));gradient[0]+=residual
    for j,a in enumerate(x,1):gradient[j]+=residual*a
   value=math.fsum(losses)/n+.001*math.fsum(a*a for a in w[1:])/2;g=[a/n+(.001*w[j] if j else 0) for j,a in enumerate(gradient)];close(value,model['final_loss']);close(math.sqrt(sum(a*a for a in g)),model['gradient_l2']);close(model['initial_loss'],math.log(2));assert model['final_loss']<=model['initial_loss']
   for result in [r for r in proof['rows'] if r['mode']==mode]:
    scores=read(result['probabilities']);rows=raw[result['case']];assert len(scores)==len(rows)
    for score,row in zip(scores,rows):
     z=w[0]+math.fsum(a*(x-m)/s for a,x,m,s in zip(w[1:],row[:d],means,stds));close(score,sigmoid(z),1e-12);probabilities+=1
   models+=1;print('GRAPH_LEARNING_MODEL_VERIFIED',episode,mode,flush=True)
 assert models==6 and len(v['rows'])==18
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL6_FOLD_PROVENANCE_TRANSFORMS_LOSSES_AND18_PREDICTIONS_VERIFIED','models':models,'raw_feature_cells':cells,'probabilities':probabilities,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(R/'tools/forecast_split_provenance_v1.py'):sha(R/'tools/forecast_split_provenance_v1.py')},'scope':'Independent real feature/fit dependency/normalizer/final objective/inference audit plus qualified trainer. No convergence optimum claim or quality/family admission.'},indent=2)+'\n');print('ALL_GRAPH_LEARNING_MODELS_VERIFIED',models,probabilities)
if __name__=='__main__':main()
