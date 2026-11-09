"""Real4 negative admission plus input/evidence substitution rejection."""
import json,tempfile,time
from pathlib import Path
from pre_route_endpoints import sha
from required_node_budget_preflight_v1 import batch_preflight,EvidenceMismatch
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'required_node_budget_preflight_v1_2026-10-09';D.mkdir(exist_ok=False);proof=E/'adder_required_node_potentials_v1_2026-10-09/verification.json';digest=sha(proof)
requests=[dict(step=i,endpoints=str(E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if i==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json'),budgets=str(E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{i}_budgets.json')) for i in range(4)]
tick=time.perf_counter();rows=batch_preflight(proof,digest,requests);seconds=time.perf_counter()-tick;negative=[]
def reject(name,p,h,qs):
 try:batch_preflight(p,h,qs)
 except EvidenceMismatch:negative.append(name)
 else:raise AssertionError('accepted '+name)
reject('wrong_proof_digest',proof,'0'*64,requests)
reject('duplicate_step',proof,digest,[requests[0],requests[0]])
qs=[dict(requests[0])];qs[0]['endpoints']=requests[1]['endpoints'];reject('cross_step_inputs',proof,digest,qs)
with tempfile.TemporaryDirectory(prefix='routecast_budget_preflight_') as tmp:
 p=Path(tmp)/'budgets.json';b=json.loads(Path(requests[0]['budgets']).read_text());b[0]['exact_delay_s']=[999999999,1];p.write_text(json.dumps(b));qs=[dict(requests[0])];qs[0]['budgets']=str(p);reject('substituted_budgets',proof,digest,qs)
assert len(rows)==4 and all(r['decision'].startswith('REJECT_CERTIFIED') for r in rows) and len(negative)==4
out=dict(bindings={str(p):sha(p) for p in (proof,Path(__file__),R/'tools/required_node_budget_preflight_v1.py')},rows=rows,negative_checks=negative,batch_seconds=seconds,routing_commands_launched=0,scope='Actual evidence-backed negative admission. Unknown/substituted evidence raises, never admits; proposed cold fallback not executed. No speedup or user-clock infeasibility claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(batch_seconds=seconds,negative_checks=negative,decisions=[r['decision'] for r in rows]),indent=2))
