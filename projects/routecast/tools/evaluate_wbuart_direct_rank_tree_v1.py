"""All9 audited outputs, original gates, and frozen baseline comparisons."""
import json
from pathlib import Path
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
from verify_wbuart_map_priority_metrics_v1 import scores
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_direct_rank_tree_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 rows=[];bindings={};frozen_rows=[]
 def bind(p):bindings[str(p)]=sha(p)
 for ep in ['episode_01','episode_02','episode_03']:
  p=D/ep/'predictions_frozen.json';proof=D/ep/'independent_verification_v1.json';v=read(p);audit=read(proof);assert audit['status']=='PASS_ALL_REAL_NODE_CANDIDATES_AND_HELDOUT_INFERENCE' and not v['heldout_labels_loaded']
  for obj in [v,audit]:assert all(sha(q)==h for q,h in obj['bindings'].items())
  assert len(v['rows'])==3 and audit['heldout_points']==25640;frozen_rows.extend(v['rows']);bind(p);bind(proof)
 workflow=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';specs=read(workflow)['comparisons'];assert len(frozen_rows)==9 and {r['case'] for r in frozen_rows}=={r['case'] for r in specs}
 halfp=E/'wbuart_paired_bbox_cart_half_v1_2026-10-20/predictions_frozen.json';leafp=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20/predictions_frozen.json';half=read(halfp)['rows'];leaf=read(leafp)['rows']
 for p in [workflow,halfp,leafp,Path(__file__),R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py',R/'tools/diagnose_wbuart_best_support_ranking_v1.py']:bind(p)
 combined=D/'all_predictions_frozen.json';assert not combined.exists();combined.write_text(json.dumps({'status':'ALL9_AUDITED_FIELDS_FROZEN_BEFORE_LABEL_EVALUATION','rows':frozen_rows,'bindings':bindings,'evaluation_labels_loaded':False},indent=2)+'\n');bind(combined)
 for r in frozen_rows:
  case=r['case'];sp=next(x['specification'] for x in specs if x['case']==case);s=read(sp);directory=Path(s['domain_proof']).parent;rp=directory/'resources.jsonl';bp=directory/'spatial_bins.json';resources=list(map(json.loads,rp.read_text().splitlines()));bins=read(bp);domain=read(s['domain_proof']);ids=read(r['resource_ids']);assert ids==sorted(x['id'] for x in resources);values=read(r['point_counts']);assert len(values)==len(ids) and all(type(x) is int and x in (0,1) for x in values)
  h=next(x for x in half if x['case']==case and x['mode']=='main');l=next(x for x in leaf if x['case']==case);assert read(h['resource_ids'])==read(l['resource_ids'])==ids
  tp=s['label_physical_audit'];raw=s['predictions']['raw_min_on']['frame'];truthcounts={int(k):v for k,v in read(tp)['node_occupancy'].items()};methods={'candidate':dict(zip(ids,values)),'fixed41_cart_half':dict(zip(ids,read(h['point_counts']))),'fixed41_spatial_leaf':dict(zip(ids,read(l['point_counts']))),'previous_native':{int(k):v for k,v in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(k):v for k,v in read(raw)['ledger'].items()}};truth=scores(resources,bins,truthcounts);reftruth=normalize(resources,bins,truthcounts);metrics={}
  for name,counts in methods.items():
   got=measure(scores(resources,bins,counts),truth,domain);ref=normalize(resources,bins,counts)
   for scope in ['resource','spatial']:
    k=domain[scope+'_k'];m=compare(ref[scope],reftruth[scope],k);assert got[scope]['hits']==round(m['precision_at_k']*k) and ((m['spearman'] is None and got[scope]['rho'] is None) or m['spearman'] is not None and got[scope]['rho'] is not None and abs(m['spearman']-got[scope]['rho'])<=1e-12)
   metrics[name]=got
  comparisons={name:{c:numeric_comparison(metrics[name],metrics[c]) for c in ['previous_native','original_H0_raw_min_on']} for name in ['candidate','fixed41_cart_half','fixed41_spatial_leaf']}
  # Independent explicit conjunction; retain original rho epsilon, K, ties.
  for name,checks in comparisons.items():
   for control,expected in checks.items():
    nonreg=[];strict=[]
    for scope in ['resource','spatial']:
     a,b=metrics[name][scope],metrics[control][scope];valid=a['rho'] is not None and b['rho'] is not None;nonreg.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
    assert expected==(all(nonreg) and any(strict))
  rows.append({'case':case,'metrics':metrics,'comparisons':comparisons,'both_original_controls':{name:all(c.values()) for name,c in comparisons.items()}})
  for p in [sp,rp,bp,s['domain_proof'],tp,s['source_frame'],raw,h['point_counts'],l['point_counts']]:bind(p)
  print('DIRECT_RANK_CASE_EVALUATED',case,rows[-1]['both_original_controls'],flush=True)
 counts={name:sum(r['both_original_controls'][name] for r in rows) for name in ['candidate','fixed41_cart_half','fixed41_spatial_leaf']};assert counts['fixed41_cart_half']==counts['fixed41_spatial_leaf']==0
 out=D/'quality_evaluation_v1.json';assert not out.exists();out.write_text(json.dumps({'status':'ALL9_AUDITED_PREDICTIONS_AND90_METRIC_VECTORS_CROSSCHECKED','rows':rows,'gate_pass_counts':counts,'all9_required':True,'bindings':bindings,'promoted':False,'scope':'Exposed WBUART retrospective quality only. Original fullpaid/native/unseen/hardware requirements remain; no automatic promotion even if numeric gate passes.'},indent=2)+'\n');print('DIRECT_RANK_QUALITY_COMPLETE',counts,flush=True)
if __name__=='__main__':main()
