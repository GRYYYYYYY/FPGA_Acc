"""Independent numeric equivalence classes, label counts and rank-sum ROC bound."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
from array import array
from fractions import Fraction as F
from prediction_metrics import compare,ranks
from verify_wbuart_best_support_ranking_v1 import normalize
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_feature_alias_classes_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'evaluation_v1.json';v=read(p);assert len(v['rows'])==18 and all(sha(path)==h for path,h in v['bindings'].items());workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons'];rows=[];vectors=0
 for row in v['rows']:
  ids=read(row['resource_ids']);blob=Path(row['raw_matrix']).read_bytes();a=array('d');a.frombytes(blob);d=row['columns'];reference=defaultdict(list)
  for i,n in enumerate(ids):reference[tuple(a[i*26:i*26+d])].append(n)
  groups=read(row['classes']);assert len(groups)==row['class_count'] and len(ids)==row['resources'] and max(len(g['RRs']) for g in groups)==row['largest_class'];assert [g['RRs'] for g in groups]==list(reference.values()) and [g['class'] for g in groups]==list(range(len(groups)))
  positions={n:i for i,n in enumerate(ids)}
  for g in groups:
   i=positions[g['RRs'][0]];assert hashlib.sha256(blob[i*26*8:(i*26+d)*8]).hexdigest()==g['signature_sha256']
  sp=next(r['specification'] for r in workflow if r['case']==row['case']);s=read(sp);labels={int(n):c for n,c in read(s['label_physical_audit'])['node_occupancy'].items()};certificate=read(row['bound_witness']);assert certificate['label_dependent'] and not certificate['admitted_predictor'] and len(certificate['classes'])==len(groups);rates={};oracle={};correct=0;conflicts=0;conflicting_resources=0
  for g,witness in zip(groups,certificate['classes']):
   ys=[labels.get(n,0) for n in g['RRs']];total=len(ys);positive=sum(ys);choice=int(positive*2>=total);rate=F(positive,total);assert witness=={'class':g['class'],'resources':total,'positive_labels':positive,'majority':choice,'oracle_rate':str(rate)};correct+=max(positive,total-positive);conflicts+=int(0<positive<total);conflicting_resources+=total*int(0<positive<total)
   for n in g['RRs']:rates[n]=rate;oracle[n]=choice
  assert len(ids)-correct==row['minimum_binary_errors'] and conflicts==row['conflicting_classes'] and conflicting_resources==row['resources_in_conflicting_classes'];ys=[labels.get(n,0) for n in ids];m=sum(ys);rs=ranks([rates[n] for n in ids]);twice_u=int(sum(2*(rank+1) for rank,y in zip(rs,ys) if y))-m*(m+1);area=F(twice_u,2*m*(len(ids)-m));assert str(area)==row['maximum_ROC_AUC'];domain=read(s['domain_proof']);directory=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (directory/'resources.jsonl').read_text().splitlines()];bins=read(directory/'spatial_bins.json');truth=normalize(resources,bins,labels);methods={'label_majority_oracle':oracle,'previous_native':{int(n):c for n,c in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(n):c for n,c in read(s['predictions']['raw_min_on']['frame'])['ledger'].items()}}
  for name,data in methods.items():
   scores=normalize(resources,bins,data);vectors+=1
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    metric=compare(scores[scope],truth[scope],k);got=row['label_majority_metrics'][name][scope];assert got['hits']==round(metric['precision_at_k']*k) and got['k']==k;assert (metric['spearman'] is None and got['rho'] is None) or metric['spearman'] is not None and abs(metric['spearman']-got['rho'])<=1e-12
  rows.append({'case':row['case'],'mode':row['mode'],'resources':len(ids),'classes':len(groups),'minimum_binary_errors':len(ids)-correct,'maximum_ROC_AUC':str(area)});print('ALIAS_BOUND_VERIFIED',row['case'],row['mode'],flush=True)
 assert len(rows)==18 and vectors==54
 out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_NUMERIC_CLASSES_BINARY_LIMITS_EXACT_ROC_AND54_ORACLE_METRICS_VERIFIED','rows':rows,'metric_vectors':vectors,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py')},'scope':'Per-case target-dependent limits and witnesses for pointwise raw-feature functions only; not deployable models, ranked-gate upper bounds, fullgraph GNN limits or new acceptance.'},indent=2)+'\n');print('ALL_FEATURE_ALIAS_BOUNDS_VERIFIED',vectors)
if __name__=='__main__':main()
