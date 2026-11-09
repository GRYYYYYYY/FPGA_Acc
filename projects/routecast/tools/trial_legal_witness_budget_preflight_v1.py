import json
from pathlib import Path
from pre_route_endpoints import sha
from legal_witness_budget_preflight_v1 import batch_preflight
from required_node_budget_preflight_v1 import EvidenceMismatch
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'legal_witness_budget_preflight_v1_2026-10-09';D.mkdir(exist_ok=False);fixture=E/'adder_legal_route_budget_fixture_v1_2026-10-09';p=fixture/'verification.json';h=sha(p);plans=json.loads((fixture/'receipt.json').read_text())['plans'];rows=batch_preflight(p,h,plans);negative=[]
for name,requests,digest in [('wrong_digest',plans,'0'*64),('duplicate_step',[plans[0],plans[0]],h),('cross_step',[{**plans[0],'budgets':plans[1]['budgets']}],h),('old_infeasible_budget',[{**plans[0],'budgets':str(E/'adder_tree_online_move_rc_budgets_2026-10-06/step_0_budgets.json')}],h)]:
 try:batch_preflight(p,digest,requests)
 except EvidenceMismatch:negative.append(name)
 else:raise AssertionError(name+' accepted')
assert len(rows)==4 and len(negative)==4
out=dict(bindings={str(f):sha(f) for f in (p,Path(__file__),R/'tools/legal_witness_budget_preflight_v1.py')},rows=rows,negative_checks=negative,routing_commands_launched=0,scope='Positive fixture admission verified; does not change original negative decision or scientific end-to-end goals.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(decisions=[r['decision'] for r in rows],negative_checks=negative),indent=2))
