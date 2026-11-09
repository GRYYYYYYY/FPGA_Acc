"""Independent raw-byte support joins and existing frozen probability/error audits."""
import json,math
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction as F
from prediction_metrics import ranks
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fold_coverage_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def area(scores,ys):
 rs=ranks(scores);p=sum(ys);return (sum(r+1 for r,y in zip(rs,ys) if y)-p*(p+1)/2)/(p*(len(ys)-p))
def main():
 p=D/'evaluation_v1.json';v=read(p);frozen=read(D/'coverage_frozen.json');assert len(v['rows'])==18 and all(sha(name)==h for name,h in v['bindings'].items());features=read(E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json')['rows'];workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];predictions=read(E/'wbuart_graph_signal_learning_v1_2026-10-20/predictions_frozen.json')['rows'];raw={};blobs={};ids={};labels={}
 for r in features:
  case=r['case'];blob=Path(r['matrix']).read_bytes();blobs[case]=blob;a=array('d');a.frombytes(blob);raw[case]=[list(a[i*26:(i+1)*26]) for i in range(r['rows'])];ids[case]=read(r['resource_ids']);s=read(next(x['specification'] for x in workflow if x['case']==case));ys={int(n):c for n,c in read(s['label_physical_audit'])['node_occupancy'].items()};labels[case]=[ys.get(n,0) for n in ids[case]]
 cache={};verified=[]
 for row in v['rows']:
  model=read(row['model']);d=len(model['mean']);key=row['model'];meta=next(r for r in frozen['rows'] if r['case']==row['case'] and r['mode']==row['mode'])
  if key not in cache:
   groups=defaultdict(lambda:[0,0]);same=defaultdict(set);columns=[[] for _ in range(d)];scores=[];ys=[];losses=[];training_keys=[]
   for case in model['training_cases']:
    for i,(x,y) in enumerate(zip(raw[case],labels[case])):
     k=blobs[case][i*26*8:(i*26+d)*8];groups[k][0]+=1;groups[k][1]+=y;training_keys.append(k);same[case.split('/')[0]].add(k)
     for j in range(d):columns[j].append(x[j])
     z=model['weights'][0]+sum(w*(a-b)/s for w,a,b,s in zip(model['weights'][1:],x[:d],model['mean'],model['std']));q=1/(1+math.exp(-z)) if z>=0 else math.exp(z)/(1+math.exp(z));scores.append(q);ys.append(y);losses.append(max(z,0)-y*z+math.log1p(math.exp(-abs(z))))
   lo=[min(x) for x in columns];hi=[max(x) for x in columns];stats=row['training_fit'];errors=sum(int(q>=.5)!=y for q,y in zip(scores,ys));assert errors==stats['binary_errors'] and len(ys)==stats['resources'];assert abs(area(scores,ys)-stats['ROC_AUC'])<=1e-15 and abs(math.fsum(losses)/len(losses)-stats['BCE'])<=1e-12;assert stats['minimum_pooled_training_alias_errors']==sum(min(positive,n-positive) for n,positive in groups.values());assert abs(area([F(groups[k][1],groups[k][0]) for k in training_keys],ys)-float(F(stats['maximum_pooled_training_alias_ROC_AUC'])))<=1e-15;cache[key]=(groups,same,lo,hi,stats)
  groups,same,lo,hi,fit_stats=cache[key];assert row['training_fit']==fit_stats;assert lo==meta['training_min'] and hi==meta['training_max'];case=row['case'];pred=next(r for r in predictions if r['case']==case and r['mode']==row['mode']);scores=read(pred['probabilities']);ys=labels[case];coverage=read(row['coverage']);assert len(coverage)==len(ids[case])==len(scores)==len(ys);counts=Counter();strata={name:dict(resources=0,model_errors=0,training_majority_diagnostic_errors=0,training_majority_predictions=0,seen_vectors_with_training_label_conflict=0) for name in row['coverage_counts']};outside=[0]*d
  for i,(node,x,y,q,entry) in enumerate(zip(ids[case],raw[case],ys,scores,coverage)):
   k=blobs[case][i*26*8:(i*26+d)*8];miss=[j for j in range(d) if x[j]<lo[j] or x[j]>hi[j]]
   for j in miss:outside[j]+=1
   category='seen_same_width' if k in same[case.split('/')[0]] else 'seen_other_width_only' if k in groups else 'unseen_outside_marginal_range' if miss else 'unseen_inside_marginal_ranges';assert entry=={'RR':node,'category':category,'training_rows_with_exact_vector':groups[k][0] if k in groups else 0};counts[category]+=1;stat=strata[category];stat['resources']+=1;stat['model_errors']+=int(int(q>=.5)!=y)
   if k in groups:
    n,positive=groups[k];stat['training_majority_predictions']+=1;stat['training_majority_diagnostic_errors']+=int(int(2*positive>=n)!=y);stat['seen_vectors_with_training_label_conflict']+=int(0<positive<n)
  assert all(counts[name]==n for name,n in row['coverage_counts'].items()) and outside==meta['outside_range_by_column'] and strata==row['strata'];stats=row['test_fit'];assert stats['binary_errors']==sum(int(q>=.5)!=y for q,y in zip(scores,ys)) and stats['resources']==len(ys) and abs(stats['ROC_AUC']-area(scores,ys))<=1e-15;assert abs(-math.fsum(math.log(q) if y else math.log1p(-q) for q,y in zip(scores,ys))/len(ys)-stats['BCE'])<=1e-12;verified.append({'case':case,'mode':row['mode'],'coverage_counts':dict(counts)});print('FOLD_COVERAGE_VERIFIED',case,row['mode'],flush=True)
 assert len(verified)==18 and len(cache)==6
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_BYTE_KEY_COVERAGE_STRATA_AND6_FROZEN_TRAIN_FITS_VERIFIED','rows':verified,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(E/'wbuart_graph_signal_learning_v1_2026-10-20/predictions_frozen.json'):sha(E/'wbuart_graph_signal_learning_v1_2026-10-20/predictions_frozen.json')},'scope':'Fixed prior models and exposed-family strata only; no new training or generalization/admission claim.'},indent=2)+'\n');print('ALL_FOLD_COVERAGES_VERIFIED')
if __name__=='__main__':main()
