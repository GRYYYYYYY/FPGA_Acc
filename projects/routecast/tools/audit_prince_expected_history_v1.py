"""Independent histogram second-moment and marginal-increment audit."""
import json,math
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_expected_history_v1_2026-10-20';X=E/'prince_paired_exposure_features_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 x=load(D/'evaluation_v1.json')
 for p,h in x['bindings'].items():assert sha(p)==h
 distributions={(r['case'],r['mode'],r['horizon'],tuple(r['key'])):{int(o):F(*p) for o,p in r['distribution'].items()} for r in load(X/'tail_projection_evaluation_v1.json')['distributions']};sums=defaultdict(lambda:defaultdict(lambda:[F(0),F(0)]));counts=defaultdict(int)
 for g in x['groups']:
  key=g['case'],g['mode'],g['horizon'];hist={int(t):n for t,n in g['target_increment_histogram'].items()};n=sum(hist.values());first=sum(t*v for t,v in hist.items());second=sum(t*t*v for t,v in hist.items());counts[key]+=n
  expected=F(0)
  if g['mode'] in ['native','hold_pres']:
   for j in range(1,g['horizon']+1):expected+=sum(((o-1)*p for o,p in distributions[g['case'],g['mode'],j,(g['mode'],j)+tuple(g['key'])].items() if o>1),F(0))
  assert expected==F(*g['predicted_increment']['tail'])
  for model,pair in g['predicted_increment'].items():
   p=F(*pair);sums[key][model][0]+=second-2*p*first+n*p*p;sums[key][model][1]+=n*p-first
 for r in x['rows']:
  key=r['case'],r['mode'],r['horizon'];assert counts[key]==r['resources']
  for model,(square,bias) in sums[key].items():
   assert math.isclose(float(square/counts[key]),r['metrics'][model]['MSE'],abs_tol=1e-14);assert math.isclose(float(bias),r['metrics'][model]['aggregate_bias'],abs_tol=1e-12)
   if r['history_held']:assert square==bias==0
 assert len(x['rows'])==48 and sum(counts.values())==714240
 out=dict(status='ALL48_HISTORY_SCORES_AND714240_GROUPED_ROWS_RECONCILED',scope='Independent second-moment algebra and tail marginal summation;integer-support and raw label recurrence validated by bound producer/prior native audit. Mean additivity does not establish a joint query-cost distribution.',bindings={str(p):sha(p) for p in [D/'evaluation_v1.json',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
