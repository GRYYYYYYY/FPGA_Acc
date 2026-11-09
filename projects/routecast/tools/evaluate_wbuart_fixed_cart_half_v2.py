"""Original gates plus separate label-dependent binary-rank counterexamples."""
import json,math
from pathlib import Path
from fractions import Fraction as F
from binary_tie_rank_limits_v1 import limits
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from verify_wbuart_map_priority_metrics_v1 import scores
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_cart_half_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def auc(values,ys):
 order=sorted(range(len(values)),key=lambda i:values[i]);negative_before=0;twice=0;i=0
 while i<len(order):
  j=i+1
  while j<len(order) and values[order[j]]==values[order[i]]:j+=1
  positive=sum(ys[k] for k in order[i:j]);negative=j-i-positive;twice+=positive*(2*negative_before+negative);negative_before+=negative;i=j
 positive=sum(ys);return twice/(2*positive*(len(ys)-positive))
def main():
 p=D/'predictions_frozen.json';v=read(p);assert len(v['rows'])==18 and not v['target_labels_read'];assert all(sha(name)==h for name,h in v['bindings'].items());workflow=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';specs=read(workflow)['comparisons'];old=read(E/'wbuart_fixed_cart_v1_2026-10-20/research_review_v1.json')['rows'];rows=[];counterexamples={};bindings={str(q):sha(q) for q in [p,workflow,Path(__file__),R/'tools/binary_tie_rank_limits_v1.py',R/'tools/diagnose_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py',E/'wbuart_fixed_cart_v1_2026-10-20/research_review_v1.json']}
 for r in v['rows']:
  sp=Path(next(x['specification'] for x in specs if x['case']==r['case']));s=read(sp);domain=read(s['domain_proof']);directory=Path(s['domain_proof']).parent;resources=[json.loads(line) for line in (directory/'resources.jsonl').read_text().splitlines()];bins=read(directory/'spatial_bins.json');ids=read(r['resource_ids']);truthcounts={int(n):c for n,c in read(s['label_physical_audit'])['node_occupancy'].items()};ys=[truthcounts.get(n,0) for n in ids];assert set(ys)=={0,1} and all(q['capacity']==1 for q in resources);points=read(r['point_counts']);soft=read(r['probabilities']);assert points==[int(p>=.5) for p in soft];truth=scores(resources,bins,truthcounts);source={int(n):c for n,c in read(s['source_frame'])['ledger'].items()};raw_path=s['predictions']['raw_min_on']['frame'];raw={int(n):c for n,c in read(raw_path)['ledger'].items()};methods={'point':dict(zip(ids,points)),'soft':{n:F.from_float(p) for n,p in zip(ids,soft)},'previous_native':source,'original_H0_raw_min_on':raw};metrics={name:measure(scores(resources,bins,data),truth,domain) for name,data in methods.items()};checks={name:numeric_comparison(metrics['point'],metrics[name]) for name in ['previous_native','original_H0_raw_min_on']};previous=next(x for x in old if x['case']==r['case'] and x['mode']==r['mode'])
  for scope in ['resource','spatial']:
   for name,oldname in [('soft','candidate'),('previous_native','previous_native'),('original_H0_raw_min_on','actual_raw_min')]:
    a,b=metrics[name][scope],previous['metrics'][oldname][scope];assert a['hits']==b['hits'] and abs(a['rho']-b['rho'])<=1e-12
  confusion={name:sum(p==pred and y==label for p,y in zip(points,ys)) for name,pred,label in [('TP',1,1),('FP',1,0),('FN',0,1),('TN',0,0)]};rows.append({'case':r['case'],'mode':r['mode'],'metrics':metrics,'comparisons':checks,'both_original_comparisons':all(checks.values()),'point_confusion':confusion,'soft_ROC_AUC':auc(soft,ys),'distinct_soft_scores':len(set(soft)),'resources':len(ids)})
  for q in [sp,Path(s['domain_proof']),directory/'resources.jsonl',directory/'spatial_bins.json',Path(s['label_physical_audit']),Path(s['source_frame']),Path(raw_path)]:bindings[str(q)]=sha(q)
  print('CART_HALF_DECISION_EVALUATED',r['case'],r['mode'],all(checks.values()),flush=True)
 main=sum(r['both_original_comparisons'] for r in rows if r['mode']=='main');ablation=sum(r['both_original_comparisons'] for r in rows if r['mode']=='ablation');out=D/'evaluation_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_CART_FIXED_CART_HALF_DECISIONS_EVALUATED','rows':rows,'main_pass':main,'ablation_pass':ablation,'bindings':bindings,'scope':'Supplemental fixed representation, not threshold tuning or replacement of original failed soft experiment. Original source/H0 raw four-metric gates preserved.  no deployable gain or family/native/fullpaid admission.'},indent=2)+'\n');print('CART_HALF_DECISION_COMPLETE',main,ablation)
if __name__=='__main__':main()
