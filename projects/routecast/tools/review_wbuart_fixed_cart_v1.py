"""Independent doubled-rank metrics and original H0 raw baseline reconciliation."""
import json
from pathlib import Path
from fractions import Fraction as F
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from verify_wbuart_map_priority_metrics_v1 import scores
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_cart_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'quality_evaluation_v1.json';v=read(p);assert all(sha(name)==h for name,h in v['bindings'].items());inventory=read(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json')['rows'];workflow=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';original=read(workflow)['comparisons'];rows=[];bindings={str(q):sha(q) for q in [p,workflow,Path(__file__),R/'tools/diagnose_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py']};vectors=0
 for row in v['rows']:
  reference=next(x for x in inventory if x['case']==row['case'] and (x['initializer'],x['timing_policy'],x['priority'])==('native_retained','warm_timing_round_updated','MAP'));resources=[json.loads(line) for line in Path(reference['resources']).read_text().splitlines()];bins=read(Path(reference['resources']).parent/'spatial_bins.json');domain=read(reference['domain_proof']);truth=scores(resources,bins,{int(n):c for n,c in read(reference['truth_payload'])['node_occupancy'].items()});ids=read(row['resource_ids']);values=read(row['probabilities']);sp=Path(next(x['specification'] for x in original if x['case']==row['case']));spec=read(sp);assert spec['source_frame']==reference['source_frame'];raw=Path(spec['predictions']['raw_min_on']['frame']);methods={'candidate':{n:F.from_float(score) for n,score in zip(ids,values)},'previous_native':{int(n):c for n,c in read(reference['source_frame'])['ledger'].items()},'actual_raw_min':{int(n):c for n,c in read(raw)['ledger'].items()}};metrics={}
  for name,data in methods.items():
   metrics[name]=measure(scores(resources,bins,data),truth,domain);vectors+=1
   if True:
    for scope in ['resource','spatial']:
     a,b=metrics[name][scope],row['metrics'][name][scope];assert a['hits']==b['hits'] and a['k']==b['k'];assert (a['rho'] is None and b['rho'] is None) or a['rho'] is not None and abs(a['rho']-b['rho'])<=1e-12
  frozen={name:numeric_comparison(metrics['candidate'],metrics[name]) for name in ['previous_native','actual_raw_min']};assert frozen==row['comparisons'] and all(frozen.values())==row['both_comparisons'];original_checks={name:numeric_comparison(metrics['candidate'],metrics[name]) for name in ['previous_native','actual_raw_min']};rows.append({'case':row['case'],'mode':row['mode'],'original_checks':original_checks,'original_gate_pass':all(original_checks.values()),'original_H0_raw_control_checks':frozen,'metrics':metrics});bindings[str(sp)]=sha(sp);bindings[str(raw)]=sha(raw)
 assert len(rows)==18 and vectors==54
 main=sum(r['original_gate_pass'] for r in rows if r['mode']=='main');ablation=sum(r['original_gate_pass'] for r in rows if r['mode']=='ablation');out=D/'research_review_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL18_FIXED_CART_FORECASTS_INDEPENDENT_RANKS_AND_ORIGINAL_H0_CONTROL_VERIFIED','rows':rows,'main_original_gate_pass':main,'ablation_original_gate_pass':ablation,'independent_metric_vectors':vectors,'bindings':bindings,'control_reconciliation':'Both producer and independent review use the original H0 raw_min_on from the original nine-case workflow. Raw features/folds are unchanged; fixed greedy CART replaces the classifier, with no fitted scaling or test-assisted selection.','scope':'Exposed-family retrospective development; no strict unseen, legality, native utility or full paid gain. Greedy depth-limited split policy is not global tree optimality. All prior logistic results retained. All cases and both model outputs retained.'},indent=2)+'\n');print('CART_QUALITY_REVIEW_COMPLETE',main,ablation)
if __name__=='__main__':main()
