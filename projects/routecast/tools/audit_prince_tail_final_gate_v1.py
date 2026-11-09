"""Independent doubled-rank and transposed-bin original-gate audit."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
from audit_prince_local_forecast_metrics_v1 import check
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_tail_final_gate_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 v=load(D/'verification.json')
 for p,h in v['bindings'].items():assert sha(p)==h
 count=0;rows=[]
 for row in v['rows']:
  if row['status']=='NO_READY_EVENT':assert not row['primary_pass'];continue
  c=row['case'];folder=E/'prince_quality_domains_v1_2026-10-20'/c.split('/')[0];resources=list(map(json.loads,(folder/'resources.jsonl').open()));bins=load(folder/'spatial_bins.json');meta=load(folder/'verification.json');spec=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'specification.json');ledger={int(n):o for n,o in load(Path(spec['label_physical_audit']))['node_occupancy'].items()};adj=defaultdict(list)
  for r in resources:
   for b in r['bins']:adj[tuple(b)].append(r['id'])
  cap={r['id']:r['capacity'] for r in resources};bc={tuple(b['key']):b['capacity'] for b in bins};truth_r={n:F(ledger.get(n,0),capacity) for n,capacity in cap.items()};truth_s={b:sum((truth_r[n]*cap[n] for n in ids),F(0))/bc[b] for b,ids in adj.items()};baseline=load(E/'prince_feedback_quality_v1_2026-10-20'/c/'comparison.json')['metrics'];gates={}
  for h,result in row['horizons'].items():
   predictions={r['id']:F(r['numerator'],r['denominator']) for r in map(json.loads,Path(result['score_file']).open())};assert set(predictions)==set(cap);assert all(0<=p<=cap[n] for n,p in predictions.items());pr={n:p/cap[n] for n,p in predictions.items()};ps={b:sum((predictions[n] for n in ids),F(0))/bc[b] for b,ids in adj.items()};measured={}
   for scope,p,t,k in [('resource',pr,truth_r,meta['resource_k']),('spatial',ps,truth_s,meta['spatial_k'])]:measured[scope]=check(p,t,k,result['metrics'][scope]);count+=1
   gates[h]={}
   for ctrl in ['previous_native','raw_min_on']:
    nonreg=[];strict=[]
    for scope in ['resource','spatial']:
     a=measured[scope];b=baseline[ctrl][scope];rho=a['spearman'];ref=b['spearman'];nonreg += [rho is not None and ref is not None and rho>=ref-1e-12,a['hits']>=b['top_k_hits']];strict += [rho is not None and ref is not None and rho>ref+1e-12,a['hits']>b['top_k_hits']]
    passed=all(nonreg) and any(strict);assert passed==result['checks'][ctrl]['pass_primary_gate'];gates[h][ctrl]=passed
   assert all(gates[h].values())==result['pass_both_controls']
  assert row['primary_pass']==all(gates['1'].values());rows.append(dict(case=c,gates=gates))
 assert count==24 and len(v['rows'])==9 and not v['full9_gate']
 out=dict(status='ALL24_FINAL_METRIC_VECTORS_AND24_CONTROL_GATES_RECONCILED',metric_vectors=count,rows=rows,primary_passes=sum(r['primary_pass'] for r in v['rows']),full9_gate=False,bindings={str(p):sha(p) for p in [D/'verification.json',Path(__file__),R/'tools/audit_prince_local_forecast_metrics_v1.py']})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'],out['primary_passes'])
if __name__=='__main__':main()
