"""Independent rational surcharge, owner release, sparse finish, stale ticket checks."""
import json,random,hashlib
from fractions import Fraction
from pathlib import Path
from restart_present_occupancy_context_v1 import Context
class Search:
 def __init__(self,caps,base):self.fields={'capacities':tuple(caps)};self.base=tuple(base);self.closed=False;self.prices={}
 def prepare(self,prices,weight,**kw):self.prices=dict(prices);assert max(prices.values())<=kw['price_ceiling']
 def patch_prices(self,p):self.prices.update(p)
def main():
 rng=random.Random(19381);checks=0
 for trial in range(60):
  caps=[rng.randrange(1,5) for _ in range(27)];base=[rng.randrange(1,1000001) for _ in caps];span={n:rng.randrange(1,8) for n in range(0,27,3)};hist={n:rng.randrange(14)+span.get(n,0) for n in range(27)};ledger={n:rng.randrange(8) for n in range(27)};s=Search(caps,base);c=Context(s,caps,base,10,span)
  for index,p in enumerate((Fraction(0),Fraction(1,2))):
   c.start_round(hist,37,ledger)
   for _ in range(8):
    owned={n for n in range(27) if ledger.get(n,0) and rng.randrange(2)};view=c.begin(owned)
    for n in range(27):
     b=base[n]*(1+hist[n]-span.get(n,0));m=max(0,ledger.get(n,0)-(n in owned)-caps[n]+1);exact=p*b*m;expected=b+exact.numerator//exact.denominator+37*span.get(n,0)-base[n]
     assert view.get(n)==expected and s.prices[n]==expected;checks+=1
    removed={n:ledger[n]-1 for n in owned if rng.randrange(3)==0};c.finish(removed);ledger.update(removed)
    try:view.get(0)
    except RuntimeError:pass
    else:raise AssertionError('stale ticket accepted')
   assert dict(c.ledger)=={n:v for n,v in ledger.items() if v}
  try:c.start_round(hist,37,ledger)
  except RuntimeError:pass
  else:raise AssertionError('third round accepted')
 r=Path(__file__).resolve().parents[1];out=r/'experiments/mmc_restart_present_context_contract_v1_2026-10-18';out.mkdir();files=[Path(__file__).resolve(),r/'tools/restart_present_occupancy_context_v1.py',r/'tools/run_native_endpoint_restart_present_v1_2026_10_18.py'];result=dict(status='fixed_restart_schedule_rational_surcharges_owner_transactions_and_bounds_pass',random_contexts=60,independent_node_checks=checks,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files});(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],checks)
if __name__=='__main__':main()
