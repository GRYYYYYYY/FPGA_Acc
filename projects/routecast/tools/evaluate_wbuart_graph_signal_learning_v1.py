"""Fixed original9-case ranking gates on frozen, independently audited models."""
import json
from pathlib import Path
from fractions import Fraction as F
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_graph_signal_learning_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=D/'independent_verification_v1.json';audit=read(proof);assert audit['models']==6 and all(sha(p)==h for p,h in audit['bindings'].items());p=D/'predictions_frozen.json';v=read(p);inventory=E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json';old=read(inventory)['rows'];cases={};rows=[];vectors=0;bindings={str(q):sha(q) for q in [proof,p,inventory,Path(__file__),R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py']}
 for row in v['rows']:
  case=row['case'];reference=next(x for x in old if x['case']==case and (x['initializer'],x['timing_policy'],x['priority'])==('native_retained','warm_timing_round_updated','MAP'))
  if case not in cases:
   resources=[json.loads(line) for line in Path(reference['resources']).read_text().splitlines()];bins=read(Path(reference['resources']).parent/'spatial_bins.json');domain=read(reference['domain_proof']);truth=normalize(resources,bins,{int(n):c for n,c in read(reference['truth_payload'])['node_occupancy'].items()});control_metrics={}
   for name,path in [('previous_native',reference['source_frame']),('actual_raw_min',reference['raw_control'])]:
    values=normalize(resources,bins,{int(n):c for n,c in read(path)['ledger'].items()});control_metrics[name]={}
    for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
     metric=compare(values[scope],truth[scope],k);control_metrics[name][scope]={'rho':metric['spearman'],'hits':round(metric['precision_at_k']*k),'k':k}
    vectors+=1
   cases[case]=(resources,bins,domain,truth,control_metrics)
   for name in ['resources','domain_proof','truth_payload','source_frame','raw_control']:bindings[reference[name]]=sha(reference[name])
   binpath=Path(reference['resources']).parent/'spatial_bins.json';bindings[str(binpath)]=sha(binpath)
  resources,bins,domain,truth,control_metrics=cases[case];ids=read(row['resource_ids']);probabilities=read(row['probabilities']);assert len(ids)==len(probabilities);counts={n:F.from_float(score) for n,score in zip(ids,probabilities)};values=normalize(resources,bins,counts);metrics={'candidate':{}}
  for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
   metric=compare(values[scope],truth[scope],k);metrics['candidate'][scope]={'rho':metric['spearman'],'hits':round(metric['precision_at_k']*k),'k':k}
  vectors+=1;metrics.update(control_metrics);checks={}
  for name in ['previous_native','actual_raw_min']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=metrics['candidate'][scope],metrics[name][scope];valid=a['rho'] is not None and b['rho'] is not None;nonreg.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   checks[name]=all(nonreg) and any(strict)
  result={**row,'metrics':metrics,'comparisons':checks,'both_comparisons':all(checks.values())};rows.append(result);print('GRAPH_LEARNING_QUALITY',case,row['mode'],result['both_comparisons'],flush=True)
 assert len(rows)==18 and vectors==36
 main=[r for r in rows if r['mode']=='main'];ablation=[r for r in rows if r['mode']=='ablation'];assert len(main)==len(ablation)==9
 out=D/'quality_evaluation_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_OUT_OF_EPISODE_PREDICTIONS_AND_ORIGINAL_DUAL_CONTROL_GATES_EVALUATED','rows':rows,'main_pass':sum(r['both_comparisons'] for r in main),'ablation_pass':sum(r['both_comparisons'] for r in ablation),'metric_vectors':vectors,'bindings':bindings,'scope':'Retrospective exposed-WBUART development only. Exact binary-float rational scores aggregated into original bins; fixed original K/ties/eps/gates. No strict unseen, legality, native utility or end-to-end gain.'},indent=2)+'\n');print('GRAPH_LEARNING_QUALITY_COMPLETE',sum(r['both_comparisons'] for r in main),sum(r['both_comparisons'] for r in ablation))
if __name__=='__main__':main()
