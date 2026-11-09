"""Fixed-observation counterfactual arithmetic; retain all verification stages."""
from pathlib import Path
from decimal import Decimal
import json
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];B=R/'experiments/sha_resident_adaptive_width_seed_complete_workflow_v1_2026-10-10';O=R/'experiments/sha_fixed_audit_floor_v1_2026-10-10';O.mkdir(exist_ok=True);bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')}
def load(p):
 v=json.loads(p.read_text(),parse_float=Decimal);bindings[str(p)]=sha(p);return v
cost=load(B/'cost_envelope.json');assert all(sha(p)==h for p,h in cost['bindings'].items());bindings.update(cost['bindings'])
audit=load(B/'seed/model/sha1/shared_audit_receipt.json');assert audit['all_three_complete_audits_pass'] and all(sha(p)==h for p,h in audit['bindings'].items());bindings.update(audit['bindings'])
handoff=load(B/'seed/handoff/sha1/receipt.json');assert all(sha(p)==h for p,h in handoff['bindings'].items());bindings.update(handoff['bindings'])
cold=Decimal(cost['rows'][0]['continuous_seconds']);other=Decimal(cost['seed_other_paid_seconds']);required=Decimal(cost['required_handoff_driver_seconds_below_at_fixed_other_costs']);a=audit['local_seconds'];assert required==cold-other and a>required
result=dict(bindings=bindings,observed_cold_seconds=str(cold),fixed_seed_other_seconds=str(other),required_driver_seconds_below=str(required),observed_independent_model_audits_local_seconds=str(a),hypothetical_seed_seconds_with_only_observed_audit_time_and_fixed_other=str(other+a),excess_over_cold_in_that_counterfactual=str(other+a-cold),search_only_optimization_insufficient_at_fixed_observed_costs=True,scope='Exact decimal arithmetic from archived single trial. Audit subcall lies inside driver, added only to disjoint outer other-cost complement, never to native controller lifetime/model/kernel clocks. Counterfactual holds audit/other costs fixed; not a physical lower bound, new execution, permission to waive audits or impossibility claim for other workloads.')
assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope']})
