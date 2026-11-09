"""Report all frozen horizons without changing original two-round acceptance."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
from external_forecast_metrics_v1 import vectors,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_fixed_horizon_trial_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert read(D/'terminal.json')['all_pass'];manifest=read(D/'manifest.json');workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');rows=[];bindings={str(p):sha(p) for p in [Path(__file__),D/'manifest.json',D/'terminal.json']}
 for c in manifest['cases']:
  cp=Path(c['output'])/'verification.json';arms=read(cp)['arms'];assert all(sha(p)==h for p,h in read(cp)['bindings'].items());spec=read(next(x['specification'] for x in workflow['comparisons'] if x['case']==c['case']));domain=read(spec['domain_proof']);folder=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');label=read(spec['label_physical_audit']);truth=vectors(resources,bins,{int(n):x for n,x in label['node_occupancy'].items()},domain['graph_nodes'],truth=True);source=read(spec['source_frame']);sm=metrics(vectors(resources,bins,{int(n):x for n,x in source['ledger'].items()},domain['graph_nodes']),truth,domain['resource_k'],domain['spatial_k'])
  for policy in ['warm_timing_frozen','warm_timing_round_updated']:
   for horizon in [2,4,8,16]:
    ms={'previous_native':sm};frames={'previous_native':spec['source_frame']}
    for method,init in [('native_retained_on','native_retained'),('raw_min_on','raw_min')]:
     arm=next(a for a in arms if a['initializer']==init and a['timing_policy']==policy);path=Path(arm['output'])/f'round{horizon-1}.json';proof=read(arm['audit']);assert proof['bindings'][str(path)]==sha(path);state=read(path);ms[method]=metrics(vectors(resources,bins,{int(n):x for n,x in state['ledger'].items()},domain['graph_nodes']),truth,domain['resource_k'],domain['spatial_k']);frames[method]=str(path)
    checks={n:gate(ms['native_retained_on'],ms[n]) for n in ['previous_native','raw_min_on']};passed=all(x['pass_primary_gate'] for x in checks.values());rows.append({'case':c['case'],'timing_policy':policy,'horizon':horizon,'metrics':ms,'frames':frames,'domain_proof':spec['domain_proof'],'label':spec['label_physical_audit'],'checks':checks,'diagnostic_same_rule_pass':passed});print(c['case'],policy,horizon,passed,flush=True)
  for p in [cp,Path(spec['source_frame']),Path(spec['label_physical_audit']),Path(spec['domain_proof']),folder/'resources.jsonl',folder/'spatial_bins.json',*[Path(a['audit']) for a in arms]]:bindings[str(p)]=sha(p)
 assert len(rows)==72
 (D/'comparison.json').write_text(json.dumps({'status':'ALL72_FIXED_HORIZON_CASE_POLICY_COMPARISONS_COMPUTED','rows':rows,'metric_vectors':216,'bindings':bindings,'scope':'All2/4/8/16 horizons reported, no best-horizon selection. Original two-round trial unchanged; longer-horizon development diagnostics, no native utility/full paid gain or unseen claim.'},indent=2,default=lambda x:{'numerator':x.numerator,'denominator':x.denominator} if isinstance(x,Fraction) else None)+'\n')
if __name__=='__main__':main()
