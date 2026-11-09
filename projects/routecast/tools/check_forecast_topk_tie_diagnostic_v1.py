import random,itertools,json
from pathlib import Path
from fractions import Fraction
from forecast_topk_tie_diagnostic_v1 import diagnose
from pre_route_endpoints import sha

def main():
 R=Path(__file__).resolve().parents[1];D=R/'experiments/forecast_topk_tie_diagnostic_contract_v1_2026-10-19';D.mkdir(exist_ok=False);rng=random.Random(128902);cases=0;pairs=0
 def selections(values,k):
  limit=sorted(values,reverse=True)[k-1];above={i for i,x in enumerate(values) if x>limit};tied={i for i,x in enumerate(values) if x==limit};return [above|set(x) for x in itertools.combinations(tied,k-len(above))]
 for n in range(1,7):
  for _ in range(50):
   a=[rng.randrange(3) for i in range(n)];b=[rng.randrange(3) for i in range(n)];k=rng.randint(1,n);pa,pb=selections(a,k),selections(b,k);expected=Fraction(sum(len(x&y) for x in pa for y in pb),len(pa)*len(pb));result=diagnose(dict(enumerate(a)),dict(enumerate(b)),k);assert Fraction(result['independent_uniform_tie_expected_hits'])==expected;cases+=1;pairs+=len(pa)*len(pb)
 files=[Path(__file__).resolve(),R/'tools/forecast_topk_tie_diagnostic_v1.py'];(D/'verification.json').write_text(json.dumps(dict(status='TIE_MARGINAL_EXPECTATION_EQUALS_EXHAUSTIVE_VALID_TOPK_SET_PAIRS',cases=cases,selection_pairs_enumerated=pairs,bindings={str(p):sha(p) for p in files},scope='Diagnostic expectation with INDEPENDENT tie selections. Even perfect identical tied score vectors need not yield1; not a replacement gate or tuned precision metric.'),indent=2)+'\n');print('PASS',cases,pairs)
if __name__=='__main__':main()
