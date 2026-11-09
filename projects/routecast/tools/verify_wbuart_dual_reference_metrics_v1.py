"""Independent exact vectors, tie ranks/topK and diagnostic gates for all108."""
import json,hashlib
from pathlib import Path
from verify_wbuart_primary_metrics_v1 import scores,rho
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_dual_reference_metrics_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());count=0;rows=[]
 for c in v['rows']:
  domain=read(c['domain_proof']);folder=Path(c['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');pred={n:scores(resources,bins,{int(k):x for k,x in read(f)['ledger'].items()}) for n,f in c['frames'].items()};gates={}
  for ref,path in c['references'].items():
   truth=scores(resources,bins,{int(k):x for k,x in read(path)['node_occupancy'].items()});computed={}
   for method,vector in pred.items():
    computed[method]={};count+=1
    for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
     r=rho(vector[scope],truth[scope]);pt=sorted(vector[scope],key=lambda n:(-vector[scope][n],n))[:k];tt=sorted(truth[scope],key=lambda n:(-truth[scope][n],n))[:k];h=len(set(pt)&set(tt));got=c['results'][ref]['metrics'][method][scope];assert got['top_k_hits']==h and got['k']==k and got['universe_size']==len(vector[scope]) and abs(got['spearman']-r)<1e-12;computed[method][scope]=(r,h)
   gates[ref]={}
   for candidate,raw in [('original_native','original_raw'),('strict_native','strict_raw')]:
    passed=[]
    for control in ['previous_native',raw]:
     nonreg=[];strict=[]
     for scope in ['resource','spatial']:
      a,h=computed[candidate][scope];b,j=computed[control][scope];nonreg.extend([a>=b-1e-12,h>=j]);strict.extend([a>b+1e-12,h>j])
     passed.append(all(nonreg) and any(strict))
    result=all(passed);assert result==c['results'][ref]['diagnostic_same_rule_checks'][candidate]['same_rule_pass'];gates[ref][candidate]=result
  rows.append({'case':c['case'],'diagnostic_same_rule_gates':gates})
 assert count==108 and len(rows)==9
 summary={ref:{method:sum(r['diagnostic_same_rule_gates'][ref][method] for r in rows) for method in ['original_native','strict_native']} for ref in ['cold','source_restart']}
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL108_DUAL_REFERENCE_VECTORS_AND_DIAGNOSTIC_GATES_INDEPENDENTLY_VERIFIED','rows':rows,'metric_vectors':108,'diagnostic_same_rule_pass_counts':summary,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'New-reference checks remain posthoc diagnostics; original cold acceptance unchanged, no promotion or generalization/gain claim.'},indent=2)+'\n');print(summary)
if __name__=='__main__':main()
