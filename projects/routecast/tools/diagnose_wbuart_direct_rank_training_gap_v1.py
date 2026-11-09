"""All18 immutable training case/fold pairs, original metrics and exact objective."""
import json
from array import array
from fractions import Fraction as F
from pathlib import Path
from direct_rank_domain_v1 import load_training_domains,training_objective
from direct_rank_objective_v1 import components
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
from verify_wbuart_map_priority_metrics_v1 import scores
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_direct_rank_training_gap_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def decode(v):
 if isinstance(v,dict):
  if set(v)=={'numerator','denominator'}:return F(v['numerator'],v['denominator'])
  return {k:decode(x) for k,x in v.items()}
 if isinstance(v,list):return [decode(x) for x in v]
 return v

def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_direct_rank_tree_v1_2026-10-20';quality=read(source/'quality_evaluation_v1.json');assert all(sha(p)==h for p,h in quality['bindings'].items());fp=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json';wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';features={r['case']:r for r in read(fp)['rows']};specs={r['case']:r['specification'] for r in read(wp)['comparisons']};rows=[];folds=[];bindings={}
 def bind(p):bindings[str(p)]=sha(p)
 for p in [Path(__file__),fp,wp,source/'quality_evaluation_v1.json',source/'research_decision_v1.json',R/'tools/direct_rank_domain_v1.py',R/'tools/direct_rank_objective_v1.py',R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py',R/'tools/diagnose_wbuart_best_support_ranking_v1.py']:bind(p)
 (D/'protocol.json').write_text(json.dumps({'policy':'All18 training case/fold pairs from frozen direct-rank trees, no refit/tuning/selection. Original rho epsilon1e-12 gates and exact training epsilon0 objective are both reported and reconciled. In-sample results never replace original heldout0/9.','bindings':bindings},indent=2)+'\n')
 for ep in ['episode_01','episode_02','episode_03']:
  mp=source/ep/'model.json';model=decode(read(mp));domains,paths=load_training_domains(R,model,features,specs);fields=[];foldrows=[]
  for p in [mp,source/ep/'independent_verification_v1.json',*paths]:bind(p)
  for case,obj in domains:
   f=features[case];ids=read(f['resource_ids']);a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assert len(a)==len(ids)*41;points=[]
   for i in range(len(ids)):
    node=0
    while model['nodes'][node]['feature']>=0:
     n=model['nodes'][node];node=n['left'] if a[i*41+n['feature']]<=n['threshold'] else n['right']
    points.append(model['nodes'][node]['state'])
   fields.append(points);s=read(specs[case]);directory=Path(s['domain_proof']).parent;resources=list(map(json.loads,(directory/'resources.jsonl').read_text().splitlines()));bins=read(directory/'spatial_bins.json');domain=read(s['domain_proof']);truthcounts={int(k):v for k,v in read(s['label_physical_audit'])['node_occupancy'].items()};raw=s['predictions']['raw_min_on']['frame'];methods={'candidate':dict(zip(ids,points)),'previous_native':{int(k):v for k,v in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(k):v for k,v in read(raw)['ledger'].items()}};truth=scores(resources,bins,truthcounts);reftruth=normalize(resources,bins,truthcounts);metrics={};exact={}
   for name,counts in methods.items():
    got=measure(scores(resources,bins,counts),truth,domain);ref=normalize(resources,bins,counts);vector=[]
    for scope in ['resource','spatial']:
     k=domain[scope+'_k'];m=compare(ref[scope],reftruth[scope],k);assert got[scope]['hits']==round(m['precision_at_k']*k) and ((m['spearman'] is None and got[scope]['rho'] is None) or m['spearman'] is not None and got[scope]['rho'] is not None and abs(got[scope]['rho']-m['spearman'])<=1e-12);vector.extend(components(ref[scope],reftruth[scope],k))
    metrics[name]=got;exact[name]=tuple(vector)
   assert exact['candidate']==obj.score(points) and [exact['previous_native'],exact['original_H0_raw_min_on']]==obj.controls
   checks={name:numeric_comparison(metrics['candidate'],metrics[name]) for name in ['previous_native','original_H0_raw_min_on']};exactchecks={name:all(x>=y for x,y in zip(exact['candidate'],exact[name])) and any(x>y for x,y in zip(exact['candidate'],exact[name])) and all(exact[t][i]!=-2 for t in ['candidate',name] for i in [0,2]) for name in checks}
   row={'fold':ep,'case':case,'metrics':metrics,'original_checks':checks,'exact_training_checks':exactchecks,'both_original_controls':all(checks.values()),'both_exact_controls':all(exactchecks.values())};rows.append(row);foldrows.append(row);bind(f['matrix']);bind(f['resource_ids']);print('DIRECT_RANK_TRAINING_PAIR_VERIFIED',ep,case,checks,flush=True)
  assert [p for field in fields for p in field]==model['points'];value=training_objective(domains,fields);assert value==tuple(model['final_objective']) and value[0]==sum(not flag for r in foldrows for flag in r['exact_training_checks'].values());folds.append({'fold':ep,'exact_failed_control_checks':value[0],'original_failed_control_checks':sum(not flag for r in foldrows for flag in r['original_checks'].values()),'training_case_both_controls_pass':sum(r['both_original_controls'] for r in foldrows),'training_cases':6,'heldout_case_both_controls_pass':sum(r['both_original_controls']['candidate'] for r in quality['rows'] if r['case'] in model['test_cases']),'heldout_cases':3})
 assert len(rows)==18
 summary={'status':'ALL18_TRAINING_PAIRS_108_METRIC_VECTORS_AND3_EXACT_OBJECTIVES_RECONCILED','rows':rows,'folds':folds,'training_both_controls_pass':sum(r['both_original_controls'] for r in rows),'training_pairs':18,'heldout_both_controls_pass':0,'heldout_cases':9,'epsilon_disagreements':sum(r['original_checks']!=r['exact_training_checks'] for r in rows),'bindings':bindings,'promoted':False,'scope':'In-sample/heldout diagnostic on exposed WBUART; no causal overfitting proof, independent-family admission or new predictor.'};(D/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print('TRAINING_GAP_COMPLETE',summary['training_both_controls_pass'],summary['epsilon_disagreements'],folds)
if __name__=='__main__':main()
