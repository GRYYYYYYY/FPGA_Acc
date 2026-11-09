"""Posthoc prior/initializer/round0/final stage metrics, no new score or fitting."""
import json,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from verify_external_zero_feedback_warm_metrics_v1 import correlation
P=R/'experiments/prospective_external_family_corrected_epoch_predictions_v1_2026-10-19';D=R/'experiments/prospective_external_family_corrected_epoch_stage_diagnosis_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 verified=read(P/'independent_metrics_verification_v1.json');assert all(sha(k)==h for k,h in verified['bindings'].items());D.mkdir(exist_ok=False);bindings={str(P/'independent_metrics_verification_v1.json'):sha(P/'independent_metrics_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';spec=read(P/case/'comparison_spec.json');proof=read(spec['domain_proof']);domain=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (domain/'resources.jsonl').read_text().splitlines()];bins=read(domain/'spatial_bins.json');truth={int(n):v for n,v in read(spec['label_physical_audit'])['node_occupancy'].items()};paths={'previous_native':Path(spec['source_frame'])}
  for method in ('raw_min_on','native_retained_on'):
   out=P/case/method;audit=read(out/'complete_event_audit.json');assert all(sha(k)==h for k,h in audit['bindings'].items());bindings[str(out/'complete_event_audit.json')]=sha(out/'complete_event_audit.json')
   for stage,name in [('initial','initial.json'),('round0','round0.json'),('final','sketch.json')]:paths[method+'/'+stage]=out/name
  def vec(ledger):
   totals=Counter()
   for r in resources:
    for key in r['bins']:totals[tuple(key)]+=ledger.get(r['id'],0)
   return {'resource':{r['id']:F(ledger.get(r['id'],0),r['capacity']) for r in resources},'spatial':{tuple(b['key']):F(totals[tuple(b['key'])],b['capacity']) for b in bins}}
  target=vec(truth);metrics={}
  for stage,path in paths.items():
   bindings[str(path)]=sha(path);frame=read(path);ledger={int(n):v for n,v in frame['ledger'].items()};prediction=vec(ledger);scores={}
   for scope,k in [('resource',proof['resource_k']),('spatial',proof['spatial_k'])]:
    a,b=prediction[scope],target[scope];keys=sorted(b);rho=correlation([a[n] for n in keys],[b[n] for n in keys]);ptop=sorted(keys,key=lambda n:(-a[n],n))[:k];ttop=sorted(keys,key=lambda n:(-b[n],n))[:k];scores[scope]=dict(spearman=rho,top_k_hits=len(set(ptop)&set(ttop)),k=k)
   metrics[stage]=scores
  r=dict(case=case,metrics=metrics);rows.append(r);print(json.dumps(r),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'diagnosis.json').write_text(json.dumps(dict(status='ALL3_PRIOR_INITIALIZER_AND_TWO_FEEDBACK_STAGE_METRICS_RECOMPUTED',rows=rows,bindings=bindings,scope='7 stages/methods x3cases x2scopes=42 metric vectors. Fixed original count/cap scores/domain/K/labels; no new scoring or oracle selection. Descriptive stage attribution, not causal mechanism proof.'),indent=2)+'\n')
if __name__=='__main__':main()
