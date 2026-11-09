"""Exact representable counterexamples:mean-only multi-step cost propagation is unidentified."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_cost_advance_ablation_trial_v1_2026-10-20';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route'
def encode(x):return json.loads(json.dumps(x,default=lambda q:dict(numerator=q.numerator,denominator=q.denominator)))
def main():
 occupancy=[[(1,F(1))],[(0,F(1,2)),(2,F(1,2))]];history=[]
 for distribution in occupancy:
  assert sum(p for o,p in distribution)==1;mean=sum(o*p for o,p in distribution);excess=sum(max(0,o-1)*p for o,p in distribution);positive=sum(p for o,p in distribution if o>0);assert excess==mean-positive;history.append(dict(mean_occupancy=mean,positive_occupancy_probability=positive,expected_excess=excess,clamped_mean=max(F(),mean-1)))
 assert history[0]['mean_occupancy']==history[1]['mean_occupancy'] and history[0]['expected_excess']!=history[1]['expected_excess']
 joint=[[(1,0,F(1,2)),(2,1,F(1,2))],[(1,1,F(1,2)),(2,0,F(1,2))]];prices=[]
 for distribution in joint:
  assert sum(p for a,f,p in distribution)==1;ma=sum(a*p for a,f,p in distribution);mf=sum(f*p for a,f,p in distribution);cross=sum(a*f*p for a,f,p in distribution);cost=sum(a*(1+f)*p for a,f,p in distribution);assert cost==ma+cross;prices.append(dict(mean_acc=ma,mean_other_owners=mf,joint_acc_other_moment=cross,expected_native_unit_base_pres1_cost=cost,product_of_means=ma*(1+mf)))
 assert prices[0]['mean_acc']==prices[1]['mean_acc'] and prices[0]['mean_other_owners']==prices[1]['mean_other_owners'] and prices[0]['expected_native_unit_base_pres1_cost']!=prices[1]['expected_native_unit_base_pres1_cost']
 out=dict(status='NECESSARY_INFORMATION_CONTRACT_WITH_EXACT_COUNTEREXAMPLES',scope='Unit-capacity configurable CHANNEL,global native history update and conditional query context. Mathematical witnesses have only exactly representable float32 operations;not empirical datasets or forecast performance.',native_history='A_next=fl32(A+fl32(alpha*max(O_phase-1,0))). With real arithmetic,expected excess=E[O_phase]-Pr(O_phase>0),not max(E[O_phase]-1,0).',native_query='At fixed conditional base B,pres p,retained ownership I:real-valued cost=B*A*(1+p*(I+F_other)). Multi-step expectation needs at least E[A] and E[A*F_other],not merely E[A] and E[F_other].',history_witness=history,joint_price_witness=prices,limitations=['Native float32 rounding generally requires additional distributional information;listed moments are not asserted sufficient for bit-exact arbitrary-state expectation.','First post-ready A is already known atready:the existing capacity-one one-step mean-other identity remains valid in its declared mathematical/implementation scope. This counterexample alone does not explain the earlier first-window learned-mean trial failures.','Phase O includes transient overcapacity uniqueNET counts;query other owners and phase ownership are distinct epochs. Keep physical ledgers integer and full-final legal occupancy score contracts unchanged.','Global history callsite excludes additional local-OPIN history semantics;nonconfigurable cost groups and capacity>1 not silently generalized.','Necessary specification for auxiliary future-state response,not original full9 global forecast/native utility/fullpaid/unseen/hardware admission.'],bindings={str(p):sha(p) for p in [Path(__file__),V/'route_common.cpp',V/'route_common.h',D/'outcome_comparison_v1.json',D/'policy_inference_verification_v2.json']})
 with (D/'cost_response_quantity_contract_v1.json').open('x') as f:json.dump(encode(out),f,indent=2);f.write('\n')
 print('EXACT_COST_RESPONSE_INFORMATION_WITNESSES_PASS')
if __name__=='__main__':main()
