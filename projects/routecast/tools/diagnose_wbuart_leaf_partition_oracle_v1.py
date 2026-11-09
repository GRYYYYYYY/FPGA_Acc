"""Target-dependent leaf-class limits/witnesses, never forecast admission."""
import json
from array import array
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from feature_alias_bounds_v1 import limits
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
from verify_wbuart_map_priority_metrics_v1 import scores
from diagnose_wbuart_best_support_ranking_v1 import measure,numeric_comparison
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_leaf_partition_oracle_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_spatial_leaf_decoder_v1_2026-10-20';p=source/'predictions_frozen.json';frozen=read(p);quality=read(source/'quality_evaluation_v1.json');features={r['case']:r for r in read(E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json')['rows']};specs={r['case']:r['specification'] for r in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons']};bindings={};rows=[]
 for name,h in frozen['bindings'].items():assert sha(name)==h
 def bind(p):bindings[str(p)]=sha(p)
 for p in [p,source/'research_review_v1.json',source/'quality_evaluation_v1.json',Path(__file__),R/'tools/feature_alias_bounds_v1.py',R/'tools/prediction_metrics.py',R/'tools/verify_wbuart_best_support_ranking_v1.py',R/'tools/verify_wbuart_map_priority_metrics_v1.py',R/'tools/diagnose_wbuart_best_support_ranking_v1.py']:bind(p)
 (D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL9_TARGET_DEPENDENT_PARTITION_DIAGNOSTIC','policy':'For each immutable heldout tree partition, use all target labels only to count leaf n,p. Exact min Hamming=sum min(p,n-p); maximum ROC AUC among all constant-on-leaf real scores by p/n ordering (qualified generic helper). Evaluate fixed per-case majority (tie1) and exact p/n witnesses with original source/H0 four metrics. No score/threshold/partition search, no selected cases.','limits':'Majority is Hamming-optimal, rate ordering is ROC-AUC-optimal; neither is claimed optimal for Spearman, TopK or spatial metrics. Failure of witnesses cannot prove original gates unattainable. Target-dependent witnesses are never deployable forecasts, never replacements for original0/9. Exposed WBUART only.','bindings':bindings},indent=2)+'\n')
 for r in frozen['rows']:
  case=r['case'];model=read(r['model']);f=features[case];ids=read(r['resource_ids']);a=array('d');a.frombytes(Path(f['matrix']).read_bytes());assert len(a)==len(ids)*41;members=defaultdict(list)
  for i,rid in enumerate(ids):
   node=0
   while model['nodes'][node]['feature']>=0:
    n=model['nodes'][node];node=n['left'] if a[i*41+n['feature']]<=n['threshold'] else n['right']
   members[node].append(rid)
  sp=specs[case];s=read(sp);tp=s['label_physical_audit'];truthcounts={int(k):v for k,v in read(tp)['node_occupancy'].items()};ys=[truthcounts.get(i,0) for i in ids];assert set(ys)=={0,1};keys=sorted(members);groups=[(len(members[k]),sum(truthcounts.get(i,0) for i in members[k])) for k in keys];bound=limits(groups);majority={};rates={};classrows=[]
  for k,(n,pos),decision,rate in zip(keys,groups,bound['majority_decisions'],bound['oracle_rates']):
   assert decision==int(pos>=n-pos) and (n-pos if decision else pos)==min(pos,n-pos)
   classrows.append({'leaf':k,'n':n,'positive':pos,'majority':decision,'rate_numerator':rate.numerator,'rate_denominator':rate.denominator})
   for i in members[k]:majority[i]=decision;rates[i]=rate
  assert sum(majority[i]!=y for i,y in zip(ids,ys))==bound['minimum_binary_errors']
  # Independent all-pairs concordance, including ties, for exact maximum AUC.
  concordance=sum(F(p1*(n2-p2))*(1 if F(p1,n1)>F(p2,n2) else F(1,2) if F(p1,n1)==F(p2,n2) else 0) for n1,p1 in groups for n2,p2 in groups)
  maxauc=concordance/(sum(ys)*(len(ys)-sum(ys)));assert maxauc==bound['maximum_ROC_AUC']
  directory=Path(s['domain_proof']).parent;rp=directory/'resources.jsonl';bp=directory/'spatial_bins.json';resources=list(map(json.loads,rp.read_text().splitlines()));bins=read(bp);domain=read(s['domain_proof']);raw=s['predictions']['raw_min_on']['frame'];inputs={'oracle_majority':majority,'oracle_rate':rates,'candidate':dict(zip(ids,read(r['point_counts']))),'previous_native':{int(k):v for k,v in read(s['source_frame'])['ledger'].items()},'original_H0_raw_min_on':{int(k):v for k,v in read(raw)['ledger'].items()}};truth=scores(resources,bins,truthcounts);reftruth=normalize(resources,bins,truthcounts);metrics={}
  for name,counts in inputs.items():
   got=measure(scores(resources,bins,counts),truth,domain);ref=normalize(resources,bins,counts)
   for scope in ['resource','spatial']:
    m=compare(ref[scope],reftruth[scope],domain[scope+'_k']);assert got[scope]['hits']==round(m['precision_at_k']*domain[scope+'_k']) and abs(got[scope]['rho']-m['spearman'])<=1e-12
   metrics[name]=got
  old=next(x for x in quality['rows'] if x['case']==case)
  for name in ['candidate','previous_native','original_H0_raw_min_on']:assert metrics[name]==old['metrics'][name]
  comparisons={name:{control:numeric_comparison(metrics[name],metrics[control]) for control in ['previous_native','original_H0_raw_min_on']} for name in ['oracle_majority','oracle_rate']}
  out=D/case;out.mkdir(parents=True);cp=out/'leaf_classes.json';cp.write_text(json.dumps(classrows,indent=2)+'\n');bind(cp)
  errors=sum(inputs['candidate'][i]!=y for i,y in zip(ids,ys));rows.append({'case':case,'classes':str(cp),'leaves':len(keys),'resources':len(ids),'minimum_binary_errors':bound['minimum_binary_errors'],'candidate_binary_errors':errors,'maximum_leaf_constant_ROC_AUC':float(maxauc),'maximum_leaf_constant_ROC_AUC_exact':str(maxauc),'metrics':metrics,'comparisons':comparisons,'witness_both_controls':{name:all(check.values()) for name,check in comparisons.items()},'admitted_predictor':False})
  for p in [r['model'],r['point_counts'],f['matrix'],r['resource_ids'],sp,tp,rp,bp,s['domain_proof'],s['source_frame'],raw]:bind(p)
  print('LEAF_ORACLE_DIAGNOSTIC',case,'min_errors',bound['minimum_binary_errors'],'actual',errors,'AUC',float(maxauc),rows[-1]['witness_both_controls'],flush=True)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_LABEL_DEPENDENT_LEAF_LIMITS_AND90_METRIC_VECTORS_CROSSCHECKED','rows':rows,'witness_gate_counts':{name:sum(r['witness_both_controls'][name] for r in rows) for name in ['oracle_majority','oracle_rate']},'bindings':bindings,'promoted':False,'original_quality_pass':0,'scope':'Target-dependent diagnostic; Hamming/AUC bounds do not bound original rho/TopK conjunction.'},indent=2)+'\n');print('ALL9_LEAF_ORACLE_COMPLETE')
if __name__=='__main__':main()
