"""All18 frozen in-sample evaluations, with independent metric crosschecks."""
import json
from array import array
from fractions import Fraction as F
from pathlib import Path
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
from verify_wbuart_map_priority_metrics_v1 import scores
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_leaf_training_metrics_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20';frozen=read(source/'predictions_frozen.json')
 for p,h in frozen['bindings'].items():assert sha(p)==h
 features={x['case']:x for x in read(E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json')['rows']};specs={x['case']:x['specification'] for x in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons']};rows=[];folds=[];bindings={}
 def bind(p):bindings[str(p)]=sha(p)
 for p in [Path(__file__),source/'predictions_frozen.json',source/'research_review_v1.json',R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py',R/'tools/diagnose_wbuart_best_support_ranking_v1.py']:bind(p)
 (D/'protocol.json').write_text(json.dumps({'scope':'All18 in-sample case/fold pairs; frozen41 trees and leaf states, no fitting or selection. Original source/H0 four-metric checks are descriptive in-sample diagnostics, never heldout quality admission. Independently compare two rank implementations, rebuild exact surrogate and reconcile original fit energies.','binding':bindings},indent=2)+'\n')
 for fold in frozen['folds']:
  dec=read(fold['decoder']);model=read(dec['original_model']);states={int(k):v for k,v in dec['states'].items()};initial={i:int(2*x['positive']>=x['rows']) for i,x in enumerate(model['nodes']) if x['feature']==-1};pooled={name:{'errors':0,'N':0,'spatial_sum':F(0),'B':0} for name in ['candidate','same_tree_half']}
  bind(fold['decoder']);bind(dec['original_model'])
  for case in model['training_cases']:
   f=features[case];ids=read(f['resource_ids']);a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assert len(a)==len(ids)*41;owners=[]
   for i in range(len(ids)):
    node=0
    while model['nodes'][node]['feature']>=0:
     x=model['nodes'][node];node=x['left'] if a[i*41+x['feature']]<=x['threshold'] else x['right']
    owners.append(node)
   points={name:dict(zip(ids,[state[k] for k in owners])) for name,state in [('candidate',states),('same_tree_half',initial)]}
   s=read(specs[case]);directory=Path(s['domain_proof']).parent;rp=directory/'resources.jsonl';bp=directory/'spatial_bins.json';resources=list(map(json.loads,rp.read_text().splitlines()));bins=read(bp);domain=read(s['domain_proof']);tp=s['label_physical_audit'];truthcounts={int(k):v for k,v in read(tp)['node_occupancy'].items()};raw=s['predictions']['raw_min_on']['frame'];methods={**points,'previous_native':{int(k):v for k,v in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(k):v for k,v in read(raw)['ledger'].items()}};truth=scores(resources,bins,truthcounts);reftruth=normalize(resources,bins,truthcounts);metrics={};losses={}
   for name,counts in methods.items():
    got=measure(scores(resources,bins,counts),truth,domain);ref=normalize(resources,bins,counts)
    for scope in ['resource','spatial']:
     k=domain[scope+'_k'];m=compare(ref[scope],reftruth[scope],k);assert got[scope]['hits']==round(m['precision_at_k']*k) and abs(got[scope]['rho']-m['spearman'])<=1e-12
    metrics[name]=got
    if name in pooled:
     errors=sum(counts[n]!=truthcounts.get(n,0) for n in ids);spatial=sum(((ref['spatial'][k]-reftruth['spatial'][k])**2 for k in ref['spatial']),F(0));q=pooled[name];q['errors']+=errors;q['N']+=len(ids);q['spatial_sum']+=spatial;q['B']+=len(bins);losses[name]={'errors':errors,'resource_error_rate':errors/len(ids),'spatial_mean_squared_error':float(spatial/len(bins))}
   checks={name:{control:numeric_comparison(metrics[name],metrics[control]) for control in ['previous_native','original_H0_raw_min_on']} for name in points}
   out=D/fold['episode']/case;out.mkdir(parents=True);p=out/'point_counts.json';p.write_text(json.dumps({name:[counts[n] for n in ids] for name,counts in points.items()})+'\n');bind(p)
   rows.append({'fold':fold['episode'],'case':case,'metrics':metrics,'losses':losses,'comparisons':checks,'in_sample_both_controls':{name:all(c.values()) for name,c in checks.items()},'points':str(p)})
   for p in [f['matrix'],f['resource_ids'],specs[case],rp,bp,s['domain_proof'],tp,s['source_frame'],raw]:bind(p)
   print('TRAINING_METRICS_VERIFIED',fold['episode'],case,rows[-1]['in_sample_both_controls'],flush=True)
  losses={name:F(q['errors'],q['N'])+q['spatial_sum']/q['B'] for name,q in pooled.items()};assert losses['candidate']==F(dec['final_energy'],dec['denominator']) and losses['same_tree_half']==F(dec['initial_energy'],dec['denominator'])
  folds.append({'fold':fold['episode'],'pooled_losses':{name:float(v) for name,v in losses.items()},'resource_error_rates':{name:q['errors']/q['N'] for name,q in pooled.items()},'spatial_mean_squared_errors':{name:float(q['spatial_sum']/q['B']) for name,q in pooled.items()}})
 summary={name:sum(r['in_sample_both_controls'][name] for r in rows) for name in ['candidate','same_tree_half']};changes={}
 for scope in ['resource','spatial']:
  for metric in ['rho','hits']:
   diffs=[r['metrics']['candidate'][scope][metric]-r['metrics']['same_tree_half'][scope][metric] for r in rows];eps=1e-12 if metric=='rho' else 0;changes[scope+'/'+metric]={'improved':sum(d>eps for d in diffs),'regressed':sum(d < -eps for d in diffs),'tied':sum(abs(d)<=eps for d in diffs)}
 assert len(rows)==18
 (D/'verification.json').write_text(json.dumps({'status':'ALL18_IN_SAMPLE_PAIRS_AND144_METRIC_VECTORS_CROSSCHECKED_EXACT_FIT_LOSSES_RECONCILED','rows':rows,'folds':folds,'in_sample_gate_counts':summary,'changes_vs_same_tree_half':changes,'bindings':bindings,'promoted':False,'scope':'In-sample diagnostics only; heldout result remains0/9, no unseen family/native/fullpaid admission.'},indent=2)+'\n');print('ALL18_TRAIN_DIAGNOSTICS_COMPLETE',summary,changes,folds)
if __name__=='__main__':main()
