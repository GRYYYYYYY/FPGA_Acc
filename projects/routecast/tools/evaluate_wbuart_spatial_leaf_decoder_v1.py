"""Original source/H0 gates and immutable same-tree half baseline, all9."""
import json
from pathlib import Path
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from verify_wbuart_map_priority_metrics_v1 import scores
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'predictions_frozen.json';proof=D/'independent_verification_v1.json';v=read(p);audit=read(proof)
 for obj in [v,audit]:assert all(sha(q)==h for q,h in obj['bindings'].items())
 assert audit['status']=='PASS_ALL3_REAL_TRACES_AND9_HELDOUT_FIELDS'
 wp=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';specs=read(wp)['comparisons'];bp=E/'wbuart_paired_bbox_cart_half_v1_2026-10-20/predictions_frozen.json';base=read(bp);rows=[];bindings={str(q):sha(q) for q in [p,proof,wp,bp,Path(__file__),R/'tools/diagnose_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py']}
 for r in v['rows']:
  sp=next(x['specification'] for x in specs if x['case']==r['case']);s=read(sp);directory=Path(s['domain_proof']).parent;rp=directory/'resources.jsonl';binp=directory/'spatial_bins.json';resources=list(map(json.loads,rp.read_text().splitlines()));bins=read(binp);domain=read(s['domain_proof']);ids=read(r['resource_ids']);points=read(r['point_counts']);assert len(ids)==len(points) and set(points)<= {0,1}
  b=next(x for x in base['rows'] if x['case']==r['case'] and x['mode']=='main');assert b['model']==r['model'] and read(b['resource_ids'])==ids
  raw=s['predictions']['raw_min_on']['frame'];truth={int(k):val for k,val in read(s['label_physical_audit'])['node_occupancy'].items()};truthscore=scores(resources,bins,truth)
  inputs={'candidate':dict(zip(ids,points)),'same_tree_half':dict(zip(ids,read(b['point_counts']))),'previous_native':{int(k):val for k,val in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(k):val for k,val in read(raw)['ledger'].items()}}
  metrics={name:measure(scores(resources,bins,data),truthscore,domain) for name,data in inputs.items()};checks={name:numeric_comparison(metrics['candidate'],metrics[name]) for name in ['previous_native','original_H0_raw_min_on']};rows.append({'case':r['case'],'metrics':metrics,'comparisons':checks,'both_original_comparisons':all(checks.values()),'same_tree_half_original_gate':all(numeric_comparison(metrics['same_tree_half'],metrics[name]) for name in checks)})
  for q in [sp,rp,binp,s['domain_proof'],s['label_physical_audit'],s['source_frame'],raw,b['point_counts']]:bindings[str(q)]=sha(q)
  print('LEAF_DECODER_QUALITY',r['case'],checks,flush=True)
 count=sum(r['both_original_comparisons'] for r in rows);baseline=sum(r['same_tree_half_original_gate'] for r in rows)
 out=D/'quality_evaluation_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL9_ORIGINAL_GATES_EVALUATED_PENDING_INDEPENDENT_METRIC_REVIEW','rows':rows,'candidate_pass':count,'same_tree_half_pass':baseline,'bindings':bindings,'promoted':False,'scope':'Retrospective exposed family; not original all9 or native/fullpaid admission.'},indent=2)+'\n');print('QUALITY_COMPLETE',count,baseline)
if __name__=='__main__':main()
