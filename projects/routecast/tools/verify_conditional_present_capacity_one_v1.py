"""Independent compiled-native scalar identity and distribution/guard fixtures."""
import json,subprocess,struct
from pathlib import Path
from pre_route_endpoints import sha
from conditional_present_capacity_one_v1 import present_bits,bits
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_query_ledger_join_v1_2026-10-20'
def main():
 old=R/'experiments/prince_owner_pressure_v2_2026-10-20';exe=old/'scalar_reference';proof=old/'verification.json';v=json.loads(proof.read_text());assert sha(exe)==v['bindings'][str(exe)];queries=[];expected={};idx=0
 for occupancy in range(65):
  for owned in [0,1]:
   if owned>occupancy:continue
   for p in [0.,.5,1.,2.,16.,208.8]:
    idx+=1;pb=bits(p);queries.append(f'{idx} {occupancy} 1 0 {pb}\n');expected[idx]=present_bits(1,owned,occupancy-owned,pb)
 result=subprocess.run([str(exe)],input=''.join(queries),text=True,capture_output=True,check=True);actual={int(i):int(word) for i,word in (line.split() for line in result.stdout.splitlines())};assert actual==expected
 rejected=0
 for cap,own,mean,p in [(2,0,1.,bits(.5)),(1,2,1.,bits(.5)),(1,0,-1.,bits(.5)),(1,0,float('nan'),bits(.5)),(1,0,float('inf'),bits(.5)),(1,0,1.,bits(-.5)),(1,0,1.,0x7f800000)]:
  try:present_bits(cap,own,mean,p)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid semantic input admitted')
 # Capacity1, I0, p.5: Bernoulli other occupancy mean.25 => expected multiplier1.125 exactly.
 assert present_bits(1,0,.25,bits(.5))==bits(1.125)
 # C2: deterministic Other1 and equiprobable Other0/Other2 have same mean1,
 # but native expected multipliers1 and1.25, so mean alone is insufficient.
 output=D/'scalar_contract_verification_v1.json';assert not output.exists();output.write_text(json.dumps(dict(status='COMPILED_NATIVE_SCALAR_IDENTITY_AND_SEMANTIC_GUARDS_PASS',compiled_native_identity_queries=len(expected),invalid_input_rejections=rejected,capacity_one_fractional_fixture={'other_mean':.25,'present':.5,'expected_multiplier':1.125},capacity_two_equal_mean_counterexample={'other_mean':1,'present':.5,'deterministic_other1_expected_multiplier':1.,'half_other0_half_other2_expected_multiplier':1.25},bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/conditional_present_capacity_one_v1.py',exe,proof]}),indent=2)+'\n');print('COMPILED_NATIVE_SCALAR_IDENTITY_PASS',len(expected),rejected)
if __name__=='__main__':main()
