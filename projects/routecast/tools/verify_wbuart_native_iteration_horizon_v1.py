"""Independent full-stage ranks/topK and source-relative checks."""
import json,hashlib
from pathlib import Path
from verify_wbuart_primary_metrics_v1 import scores,rho
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_native_iteration_horizon_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());count=0;summary=[]
 for row in v['rows']:
  domain=read(row['domain_proof']);folder=Path(row['domain_proof']).parent;resources=[json.loads(s) for s in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');truth={int(n):x for n,x in read(row['label_physical_audit'])['node_occupancy'].items()};target=scores(resources,bins,truth);source=scores(resources,bins,{int(n):x for n,x in read(row['source_frame'])['ledger'].items()});control={};fixed=[]
  for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
   t=sorted(target[scope],key=lambda n:(-target[scope][n],n))[:k];a=source[scope];control[scope]=(rho(a,target[scope]),len(set(sorted(a,key=lambda n:(-a[n],n))[:k])&set(t)),t)
  for stage in row['stages']:
   ledger={int(n):x for n,x in stage['ledger'].items()};vectors=scores(resources,bins,ledger);nonreg=[];strict=[]
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    a=vectors[scope];r=rho(a,target[scope]);c,h,t=control[scope];hits=len(set(sorted(a,key=lambda n:(-a[n],n))[:k])&set(t));got=stage['metrics'][scope];assert got['top_k_hits']==hits and got['k']==k and ((r is None and got['spearman'] is None) or (r is not None and abs(got['spearman']-r)<1e-12));nonreg.extend([r is not None and c is not None and r>=c-1e-12,hits>=h]);strict.extend([r is not None and c is not None and r>c+1e-12,hits>h])
   passed=all(nonreg) and any(strict);assert passed==stage['same_rule_vs_source']['pass_primary_gate'];assert stage['CHANNEL_occupancy_L1_error']==sum(abs(ledger.get(r['id'],0)-truth.get(r['id'],0)) for r in resources);count+=1
   if stage['tag']=='iteration_end_after_local_opins' and stage['iteration']<=2:fixed.append({'iteration':stage['iteration'],'same_rule_vs_source':passed})
  summary.append({'case':row['case'],'reference':row['reference'],'first_two':fixed,'iterations':len(row['stages'])-2})
 assert len(summary)==18 and count==v['stages']
 (D/'independent_metrics_verification_v1.json').write_text(json.dumps({'status':'ALL_NATIVE_STAGE_METRICS_AND_FIXED_FIRST_TWO_CHECKS_INDEPENDENTLY_VERIFIED','stages':count,'rows':summary,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Independent score/rank/L1 arithmetic on reconstructed ledgers; producer checkpoint parser reused from authenticated trace evidence, not independent per-event physical tree audit.'},indent=2)+'\n');print('VERIFIED_STAGES',count)
if __name__=='__main__':main()
