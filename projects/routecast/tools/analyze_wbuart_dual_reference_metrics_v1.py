"""Fixed-domain posthoc dual reference analysis; original cold gates unchanged."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
from external_forecast_metrics_v1 import vectors,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_dual_reference_metrics_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';P=E/'wbuart_target_source_restart_reference_v1_2026-10-20/reference_review_v1.json';bindings={str(p):sha(p) for p in [Path(__file__),W,P]};rows=[]
 for c in read(W)['comparisons']:
  s=read(c['specification']);domain=read(s['domain_proof']);folder=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');case=c['case'];strict=read(E/'wbuart_strict_progress_trial_v1_2026-10-20'/case/'warm_timing_round_updated_specification.json');warm=E/'wbuart_warm_inputs_v1_2026-10-20'/case/'native_retained/initial.json';frames={'previous_native':s['source_frame'],'warm':str(warm),'original_native':s['predictions']['native_retained_on']['frame'],'original_raw':s['predictions']['raw_min_on']['frame'],'strict_native':strict['predictions']['native_retained_on']['frame'],'strict_raw':strict['predictions']['raw_min_on']['frame']};ledgers={name:{int(n):x for n,x in read(p)['ledger'].items()} for name,p in frames.items()};seeded=E/'wbuart_target_source_restart_reference_v1_2026-10-20'/case;proof=read(seeded/'verification.json');assert proof['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and all(sha(p)==h for p,h in proof['bindings'].items());assert proof['bindings'][str(seeded/'physical_audit.json')]==sha(seeded/'physical_audit.json');refs={'cold':s['label_physical_audit'],'source_restart':str(seeded/'physical_audit.json')};result={}
  for ref,p in refs.items():
   label=read(p);assert label['overflow_units']==0;truth=vectors(resources,bins,{int(n):x for n,x in label['node_occupancy'].items()},domain['graph_nodes'],truth=True);ms={name:metrics(vectors(resources,bins,ledger,domain['graph_nodes']),truth,domain['resource_k'],domain['spatial_k']) for name,ledger in ledgers.items()};checks={}
   for candidate,raw in [('original_native','original_raw'),('strict_native','strict_raw')]:checks[candidate]={'vs_source':gate(ms[candidate],ms['previous_native']),'vs_raw':gate(ms[candidate],ms[raw])};checks[candidate]['same_rule_pass']=checks[candidate]['vs_source']['pass_primary_gate'] and checks[candidate]['vs_raw']['pass_primary_gate']
   result[ref]={'metrics':ms,'diagnostic_same_rule_checks':checks}
  original=read(c['comparison']);newstrict=read(E/'wbuart_strict_progress_trial_v1_2026-10-20'/case/'warm_timing_round_updated_comparison.json')
  for method,prior in [('original_native',original),('strict_native',newstrict)]:
   assert result['cold']['diagnostic_same_rule_checks'][method]['same_rule_pass']==prior['pass_case_gate']
   for scope in ['resource','spatial']:
    a,b=result['cold']['metrics'][method][scope],prior['metrics']['native_retained_on'][scope];assert abs(a['spearman']-b['spearman'])<1e-12 and a['top_k_hits']==b['top_k_hits']
  rows.append({'case':case,'frames':frames,'references':refs,'domain_proof':s['domain_proof'],'results':result})
  for p in [Path(c['specification']),Path(s['domain_proof']),folder/'resources.jsonl',folder/'spatial_bins.json',seeded/'verification.json',*map(Path,frames.values()),*map(Path,refs.values())]:bindings[str(p)]=sha(p)
  print(case,{ref:{n:x['same_rule_pass'] for n,x in r['diagnostic_same_rule_checks'].items()} for ref,r in result.items()},flush=True)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL108_FIXED_DOMAIN_DUAL_REFERENCE_METRIC_VECTORS_COMPUTED','rows':rows,'metric_vectors':108,'bindings':bindings,'scope':'Posthoc diagnostic source-restart reference versus unchanged original cold labels. Same-rule diagnostic checks on new reference are not original trial acceptance or candidate promotion; no tuning, new scores, case filtering or full paid gain.'},indent=2,default=lambda x:{'numerator':x.numerator,'denominator':x.denominator} if isinstance(x,Fraction) else None)+'\n')
if __name__=='__main__':main()
