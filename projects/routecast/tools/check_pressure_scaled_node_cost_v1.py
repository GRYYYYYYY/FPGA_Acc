"""Exhaustive exact Fraction cost and original factor1 control parity."""
import json,itertools,hashlib
from pathlib import Path
from fractions import Fraction as F
from pressure_scaled_node_cost_v1 import cost
from multiplicative_net_congestion_v1 import cost as original
R=Path(__file__).resolve().parents[1];D=R/'experiments/pressure_scaled_node_cost_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);count=0;invalid=0
 for base,h,occ,cap,owner,span,factor in itertools.product([0,1,5,17],[0,2],range(8),[0,1,3],[False,True],[0,3],[F(0),F(1,2),F(1)]):
  if (owner and occ==0) or (occ and cap==0):
   try:cost(base,h,occ,cap,factor,owner,span)
   except ValueError:invalid+=1
   else:raise AssertionError('invalid ownership')
   continue
  value=cost(base,h,occ,cap,factor,owner,span);other=occ-int(owner);exact=F(base)*(1+h)*(1+factor*max(0,other-cap+1))+span;assert value-1<exact<=value
  if factor==1:assert value==original(base,h,occ,cap,owner,span)
  if factor==0:assert value==base*(1+h)+span
  count+=1
 for factor in [F(-1),.5,True]:
  try:cost(1,0,0,1,factor)
  except ValueError:invalid+=1
  else:raise AssertionError('factor domain')
 files=[Path(__file__),R/'tools/pressure_scaled_node_cost_v1.py',R/'tools/multiplicative_net_congestion_v1.py',R/'experiments/wbuart_native_present_factor_design_v1_2026-10-20/protocol.json'];(D/'verification.json').write_text(json.dumps({'status':'EXHAUSTIVE_FACTOR_COST_CONTROL_OWNER_DOMAIN_AND_FRACTION_CEIL_PASS','valid_cases':count,'invalid_rejections':invalid,'bindings':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Arithmetic contract only; full real graph/context/native float and quality equivalence not claimed.'},indent=2)+'\n');print('VALID',count,'REJECTED',invalid)
if __name__=='__main__':main()
