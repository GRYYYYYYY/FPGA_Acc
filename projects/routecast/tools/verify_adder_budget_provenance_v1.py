"""Full archived four-step budget provenance, never reinterpret model limits as user clocks."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_budget_provenance_v1_2026-10-08';D.mkdir(exist_ok=False)
B=E/'adder_tree_online_move_rc_budgets_2026-10-06';p=json.loads((B/'protocol.json').read_text());r=json.loads((B/'receipt.json').read_text());assert r['protocol_sha256']==sha(B/'protocol.json')
Q=E/'adder_tree_online_dynamic_net_quality_2026-10-06';qr=json.loads((Q/'receipt.json').read_text());assert sha(Q/'receipt.json')==p['quality_receipt_sha256']
bindings={str(B/'protocol.json'):sha(B/'protocol.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(Q/'receipt.json'):sha(Q/'receipt.json')}
for n,h in p['sources'].items():assert sha(B/'sources'/n)==h;bindings[str(B/'sources'/n)]=h
rows=[]
for step in r['steps']:
 k=step['step'];bp=B/f'step_{k}_budgets.json';assert sha(bp)==step['budget_sha256'];budgets=json.loads(bp.read_text())
 pred=E/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if k==0 else E/'adder_tree_2L032_move_sequence_audit_2026-10-06'/f'step_{k}_prediction.json'
 assert sha(pred)==step['reference_prediction_sha256'];prediction=json.loads(pred.read_text())
 metric=Q/f'step_{k}'/'connections.json'
 if not metric.exists():
  q=next(x for x in qr['results'] if int(x['design'].split('_')[1])==k);metric=Q/q['design']/'connections.json'
 assert sha(metric)==step['oracle_report_sha256'];metrics={x['connection_id']:x for x in json.loads(metric.read_text())};queries={x['connection_id']:x for x in prediction['connections']}
 assert len(queries)==len(prediction['connections'])==len(budgets)==step['connections']
 assert {x['connection_id'] for x in budgets}==set(queries)==set(metrics)
 for b in budgets:
  q=queries[b['connection_id']]
  assert all(b[n]==q[n] for n in ('connection_id','net_id','source','sink'))
  delay=F(*b['exact_delay_s']);assert delay==F(metrics[b['connection_id']]['old_rc_s_exact'])
  assert F(b['scaled_integer_budget'],r['integer_scale'])==delay
 for f in (bp,pred,metric):bindings[str(f)]=sha(f)
 rows.append(dict(step=k,connections=len(budgets),complete_identity_and_exact_oracle_budget_parity=True,budget_origin='fixed_same_placement_predictor_path_delay',user_clock_constraint=False,independent_native_route_budget_success_proved=False))
assert len(rows)==4 and sum(x['connections'] for x in rows)==2064
bindings[str(Path(__file__))]=sha(Path(__file__))
report=dict(bindings=bindings,rows=rows,scope=p['scope'],total_connections=2064,all_existing_budgets_unchanged=True,selection='Eligible only for explicitly scoped model-baseline nonregression research. No user-clock feasible continue or unseen family; budgets derive from baseline paths and cannot serve independent timing targets.',real_native_continue_verified=False)
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'},indent=2))
