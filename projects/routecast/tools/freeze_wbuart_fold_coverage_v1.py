"""Exact feature support and marginal range coverage, no target label reads."""
import json,math
from pathlib import Path
from array import array
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fold_coverage_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json';proof=E/'wbuart_graph_signal_learning_v1_2026-10-20/independent_verification_v1.json';features=read(source);assert all(sha(p)==h for p,h in features['bindings'].items());assert all(sha(p)==h for p,h in read(proof)['bindings'].items());raw={};ids={}
 for r in features['rows']:
  a=array('d');a.frombytes(Path(r['matrix']).read_bytes());raw[r['case']]=[tuple(a[i*26:(i+1)*26]) for i in range(r['rows'])];ids[r['case']]=read(r['resource_ids'])
 bindings={str(p):sha(p) for p in [source,proof,Path(__file__)]};(D/'protocol.json').write_text(json.dumps({'policy':'Existing frozen leave-one-episode-out folds and main26/ablation11. Exact raw feature equality against training6 and same-width training2. For unseen exact vectors, identify whether any coordinate falls outside training marginal min/max. No radius, nearest-neighbor, normalization fit, labels or new classifier.','scope':'Exact novelty is not itself out-of-distribution or evidence of inability to interpolate. Marginal range coverage is not joint coverage or generalization proof. Exposed WBUART only.','bindings':bindings},indent=2)+'\n');rows=[]
 for episode in ['episode_01','episode_02','episode_03']:
  for mode,d in [('main',26),('ablation',11)]:
   model_path=E/'wbuart_graph_signal_learning_v1_2026-10-20'/episode/mode/'model.json';model=read(model_path);training=model['training_cases'];testing=model['test_cases'];index={};by_width={}
   for case in training:
    width=case.split('/')[0];by_width.setdefault(width,set())
    for row in raw[case]:key=row[:d];index[key]=index.get(key,0)+1;by_width[width].add(key)
   low=[min(row[j] for case in training for row in raw[case]) for j in range(d)];high=[max(row[j] for case in training for row in raw[case]) for j in range(d)]
   for case in testing:
    classes=[];outside=[0]*d
    for node,row in zip(ids[case],raw[case]):
     key=row[:d];miss=[j for j in range(d) if not low[j]<=row[j]<=high[j]]
     for j in miss:outside[j]+=1
     category='seen_same_width' if key in by_width[case.split('/')[0]] else 'seen_other_width_only' if key in index else 'unseen_outside_marginal_range' if miss else 'unseen_inside_marginal_ranges';classes.append({'RR':node,'category':category,'training_rows_with_exact_vector':index.get(key,0)})
    directory=D/episode/mode/case;directory.mkdir(parents=True);p=directory/'coverage.json';p.write_text(json.dumps(classes,separators=(',',':'))+'\n');counts={name:sum(q['category']==name for q in classes) for name in ['seen_same_width','seen_other_width_only','unseen_inside_marginal_ranges','unseen_outside_marginal_range']};rows.append({'case':case,'mode':mode,'model':str(model_path),'training_cases':training,'coverage':str(p),'resources':len(classes),'counts':counts,'outside_range_by_column':outside,'training_min':low,'training_max':high});bindings[str(p)]=sha(p);bindings[str(model_path)]=sha(model_path)
 assert len(rows)==18
 (D/'coverage_frozen.json').write_text(json.dumps({'status':'ALL18_INPUT_ONLY_FOLD_COVERAGE_PARTITIONS_FROZEN','rows':rows,'target_labels_read':False,'bindings':bindings},indent=2)+'\n');print('ALL18_FOLD_COVERAGES_FROZEN')
if __name__=='__main__':main()
