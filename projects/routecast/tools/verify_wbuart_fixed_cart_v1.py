"""Independent full-data grouped-value Gini search at every real tree node."""
import json,math
from pathlib import Path
from array import array
from collections import defaultdict
from fractions import Fraction as F
from forecast_split_provenance_v1 import check
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_cart_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'predictions_frozen.json';v=read(p);manifest=read(D/'manifest.json');features=read(manifest['features']);inventory=read(manifest['inventory'])['rows'];raw={};models=[];probabilities=0;node_total=0
 for doc in [v,manifest,features]:assert all(sha(path)==h for path,h in doc['bindings'].items())
 for r in features['rows']:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());raw[r['case']]=[list(a[i*26:(i+1)*26]) for i in range(r['rows'])]
 for episode in ['episode_01','episode_02','episode_03']:
  fold=D/episode;proof=read(fold/'verification.json');assert not proof['test_labels_loaded'] and all(sha(path)==h for path,h in proof['bindings'].items());provenance=read(fold/'fit_provenance.json');assert check(provenance['declarations'])==provenance['preflight'] and provenance['declarations']['feature_normalizer_fit_samples']==[];training=sorted(case for case in raw if not case.endswith(episode));testing=sorted(case for case in raw if case.endswith(episode));assert provenance['declarations']['model_fit_samples']==training
  for case in testing:assert next(r['truth_payload'] for r in inventory if r['case']==case) not in proof['bindings']
  Y=[]
  for case in training:
   target={int(n):c for n,c in read(next(r['truth_payload'] for r in inventory if r['case']==case))['node_occupancy'].items()};r=next(r for r in features['rows'] if r['case']==case);Y.extend(target.get(n,0) for n in read(r['resource_ids']))
  for mode,d in [('main',26),('ablation',11)]:
   model_path=fold/mode/'model.json';model=read(model_path);assert model['depth_limit']==8 and model['minimum_child_rows']==64 and model['columns_count']==d and model['columns']==features['columns'][:d] and model['training_cases']==training and model['test_cases']==testing;X=[row[:d] for case in training for row in raw[case]];N=len(X);assert model['training_rows']==N;nodes=model['nodes'];leaves=[];seen=set()
   def visit(at,members,depth):
    assert at not in seen and 0<=at<len(nodes);seen.add(at);node=nodes[at];positive=sum(Y[i] for i in members);size=len(members);assert node['rows']==size and node['positive']==positive;best=F(positive*positive,size);winner=None
    if depth<8 and size>=128 and 0<positive<size:
     for f in range(d):
      grouped=defaultdict(lambda:[0,0])
      for i in members:grouped[X[i][f]][0]+=1;grouped[X[i][f]][1]+=Y[i]
      left_n=0;left_p=0
      for value in sorted(grouped)[:-1]:
       n,pos=grouped[value];left_n+=n;left_p+=pos;right_n=size-left_n;right_p=positive-left_p
       if min(left_n,right_n)<64:continue
       score=F(left_p*left_p,left_n)+F(right_p*right_p,right_n)
       if score>best:best=score;winner=(f,value)
    if winner is None:
     assert node['feature']==node['left']==node['right']==-1 and node['threshold']==0;leaves.append(node);return at+1
    f,value=winner;assert node['feature']==f and node['threshold']==value and node['left']==at+1;left=[i for i in members if X[i][f]<=value];right=[i for i in members if X[i][f]>value];after=visit(node['left'],left,depth+1);assert node['right']==after;return visit(node['right'],right,depth+1)
   assert visit(0,list(range(N)),0)==len(nodes) and len(seen)==len(nodes);node_total+=len(nodes);errors=sum(min(node['positive'],node['rows']-node['positive']) for node in leaves);train_BCE=sum(-node['positive']*math.log((node['positive']+1)/(node['rows']+2))-(node['rows']-node['positive'])*math.log((node['rows']-node['positive']+1)/(node['rows']+2)) for node in leaves)/N
   for result in [r for r in proof['rows'] if r['mode']==mode]:
    values=read(result['probabilities']);rows=raw[result['case']];assert len(values)==len(rows)
    for value,row in zip(values,rows):
     at=0
     while nodes[at]['feature']!=-1:
      node=nodes[at];at=node['left'] if row[node['feature']]<=node['threshold'] else node['right']
     node=nodes[at];assert value==float(F(node['positive']+1,node['rows']+2));probabilities+=1
   models.append({'episode':episode,'mode':mode,'nodes':len(nodes),'leaves':len(leaves),'train_resources':N,'training_half_errors':errors,'training_error_fraction':errors/N,'training_BCE':train_BCE});print('REAL_CART_ALL_SPLITS_VERIFIED',episode,mode,len(nodes),errors,flush=True)
 assert len(models)==6 and len(v['rows'])==18
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL6_REAL_CART_FULL_GREEDY_SPLITS_FIT_DEPENDENCIES_AND18_PREDICTIONS_VERIFIED','models':6,'model_rows':models,'tree_nodes':node_total,'probabilities':probabilities,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(R/'tools/forecast_split_provenance_v1.py'):sha(R/'tools/forecast_split_provenance_v1.py')},'scope':'Exact frozen greedy policy on training rows, not global tree optimality. Train-only labels/no transforms; no original quality/native/family admission.'},indent=2)+'\n');print('ALL_REAL_CARTS_VERIFIED',node_total,probabilities)
if __name__=='__main__':main()
