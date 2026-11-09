"""Exact Fraction cutoff tie diagnostics only; original deterministic gates unchanged."""
import json,hashlib
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_corrected_epoch_predictions_v1_2026-10-19';D=E/'prospective_external_family_corrected_spatial_tie_audit_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 v=read(P/'independent_metrics_verification_v1.json');assert all(sha(k)==h for k,h in v['bindings'].items());D.mkdir(exist_ok=False);bindings={str(P/'independent_metrics_verification_v1.json'):sha(P/'independent_metrics_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';spec=read(P/case/'comparison_spec.json');domain=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (domain/'resources.jsonl').read_text().splitlines()];bins=read(domain/'spatial_bins.json');cap={tuple(b['key']):b['capacity'] for b in bins};keys=sorted(cap)
  def vector(ledger):
   totals=Counter()
   for r in resources:
    for key in r['bins']:totals[tuple(key)]+=ledger.get(r['id'],0)
   return {k:F(totals[k],cap[k]) for k in keys}
  truthpath=Path(spec['label_physical_audit']);truth=vector({int(n):x for n,x in read(truthpath)['node_occupancy'].items()});truthorder=sorted(keys,key=lambda k:(-truth[k],k));cut=truth[truthorder[19]];ties={k for k in keys if truth[k]==cut};strict={k for k in keys if truth[k]>cut};true20=set(truthorder[:20]);stages={}
  paths={'prior':Path(spec['source_frame']),'warm':P/case/'native_retained_on/initial.json','round0':P/case/'native_retained_on/round0.json','final':P/case/'native_retained_on/sketch.json'}
  for stage,path in paths.items():
   vec=vector({int(n):x for n,x in read(path)['ledger'].items()});order=sorted(keys,key=lambda k:(-vec[k],k));top=order[:20];p_cut=vec[top[-1]];stages[stage]=dict(original_deterministic_hits=len(set(top)&true20),selected_at_or_above_truth_cutoff=sum(truth[k]>=cut for k in top),selected_below_truth_cutoff=sum(truth[k]<cut for k in top),selected_prediction_over1=sum(vec[k]>1 for k in top),prediction_cutoff=str(p_cut),prediction_cutoff_ties=sum(vec[k]==p_cut for k in keys),truth_score_of_selected_bins=[str(truth[k]) for k in top]);bindings[str(path)]=sha(path)
  rows.append(dict(case=case,truth_K=20,truth_cutoff=str(cut),truth_strictly_above_cutoff=len(strict),truth_cutoff_ties=len(ties),stages=stages));bindings[str(truthpath)]=sha(truthpath)
  for p in (domain/'resources.jsonl',domain/'spatial_bins.json'):bindings[str(p)]=sha(p)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_EXACT_SPATIAL_CUTOFF_TIES_AND_DETERMINISTIC_HITS_DIAGNOSED',rows=rows,bindings=bindings,scope='Descriptive exact Fraction audit. Original fixed-ID top20 metric and quality failure remain authoritative. Cutoff equivalence is not a replacement gate, new acceptance score, calibrated probability or future selection rule.'),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
