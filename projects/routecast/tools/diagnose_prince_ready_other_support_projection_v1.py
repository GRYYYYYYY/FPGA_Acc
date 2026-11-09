"""Post-screen fixed support-bound diagnostic; original frozen candidate stays rejected."""
import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import final_inverse,L
R=Path(__file__).resolve().parents[1];S=R/'experiments/prince_ready_owner_forecast_v1_2026-10-20';D=R/'experiments/prince_ready_other_support_projection_v1_2026-10-20'
def main():
 assert not D.exists();D.mkdir();source=S/'verification.json';v=json.loads(source.read_text());bindings={str(source):sha(source),str(__file__):sha(__file__)}
 (D/'protocol.json').write_text(json.dumps(dict(status='POST_SCREEN_DEVELOPMENT_DIAGNOSIS_NOT_PROSPECTIVE',candidate='Project already coherent ready OTHER-NET forecast F to min(F,1). Unit cap comes from fixed graph/feasible legal target support, never optimized from labels.',quantity='Advisory conditional demand forecast only; no physical ownership ledger modified, no global future ownership consistency asserted.',analysis='For Y in[0,1], clipping F>=0 reduces absolute error by exactly max(F-1,0). Compare analytic error deduction with direct terminal-ledger oracle rescoring.',original_candidate='Frozen unclipped ready-owner persistence remains rejected; no readiness threshold tuning.',bindings=bindings),indent=2)+'\n');rows=[]
 for row in v['rows']:
  if not row['available']:rows.append(dict(case=row['case'],available=False,reason=row['reason']));continue
  inp=Path(row['input_path']);assert sha(inp)==row['input_sha256'];lp=L/row['case']/'capture/queries.tsv.ledger.bin';oracle=final_inverse(lp);call_reduction=direct_call=0;pair={}
  for net,node,ident,pred,base,count in map(json.loads,inp.open()):
   target=len(oracle[node]-{net});assert target in [0,1];bounded=min(pred,1);call_reduction+=count*max(pred-1,0);direct_call+=count*abs(bounded-target);pair[net,node]=(pred,bounded,target)
  pair_reduction=sum(max(pred-1,0) for pred,bounded,target in pair.values());direct_pair=sum(abs(bounded-target) for pred,bounded,target in pair.values());analytic_call=row['call_error_ready_owner']-call_reduction;analytic_pair=Fraction(*row['pair_error_ready_owner'])-pair_reduction;assert analytic_call==direct_call and analytic_pair==direct_pair
  rows.append(dict(case=row['case'],available=True,queries=row['calls'],pairs=row['unique_NET_node_pairs'],support_excess_call_mass=call_reduction,support_excess_pair_mass=pair_reduction,projected_call_error=direct_call,persistence_call_error=row['call_error_persistence'],projected_pair_error=direct_pair,persistence_pair_error=row['pair_error_persistence'],call_strictly_better=direct_call<row['call_error_persistence'],pair_strictly_better=direct_pair<Fraction(*row['pair_error_persistence'])));bindings[str(inp)]=sha(inp);bindings[str(lp)]=sha(lp)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='SUPPORT_BOUND_ANALYTIC_AND_DIRECT_ERRORS_MATCH',rows=rows,bindings=bindings),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
