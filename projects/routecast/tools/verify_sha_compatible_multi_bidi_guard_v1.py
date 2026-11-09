"""Complete new-policy live model audits; floor parity only, not old-state parity."""
from pathlib import Path
from collections import Counter
import ast,json
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/sha_compatible_multi_bidi_guard_v1_2026-10-10';M=O/'model';B=R/'experiments/sha_overflow_guard_v1_2026-10-10/second_swap/model';bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
for p in [R/'experiments/compatible_multi_bidi_contract_v1_2026-10-10/verification.json',M/'shared_audit_receipt.json']:
 v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
audit=json.loads((M/'verification.json').read_text());assert audit['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and audit['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
r=json.loads((M/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items()) and all(sha(p)==h for p,h in r['files'].items());bindings.update(r['bindings']);bindings.update(r['files'])
floor=M/'floors.json';base=B/'floors.json';assert json.loads(floor.read_text())==json.loads(base.read_text());initial=json.loads((M/'initial.json').read_text());final=json.loads((M/'sketch.json').read_text());assert initial['completed_connections']==final['completed_connections']==6273 and len(initial['records'])==len(final['records'])==6273
events=[e for row in r['rounds'] for e in row['events']];assert len(events)==4507;metrics=json.loads((M/'multi_bidi_metrics.json').read_text());assert metrics['stats']['requests']==7468 and metrics['stats']['merged']==1907
old=R/'tools/run_resident_overflow_guard_model_v1.py';new=R/'tools/run_compatible_multi_bidi_guard_model_v1.py'
def loops(p):
 f=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='predict');return [ast.dump(n) for n in f.body if isinstance(n,ast.For)]
assert loops(old)==loops(new)
for p in [M/'receipt.json',M/'verification.json',floor,base,old,new]:bindings[str(p)]=sha(p)
w=R/'experiments/compatible_multi_bidi_contract_v1_2026-10-10/parent_conflict_witness.json';bindings[str(w)]=sha(w)
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_query_floors_equal_original=True,all_complete_new_policy_physical_states_events_prices_epochs_ledgers_pass=True,initial_feedback_loops_AST_unchanged=True,events=len(events),statuses=dict(Counter(e['status'] for e in events)),metrics=metrics,estimate_overflow=[initial['overflow_units'],*[x['overflow_after'] for x in r['rounds']]],old_guard_final_overflow=1437,local_model_seconds=r['total_paid_resident_seconds'],scope='New path/tie policy on exposed SHA; own complete endogenous feedback. Final estimate1480 vs old1437, not improved quality/transparent replacement. No native64, seed/fullworkflow, realgraph conflict fallback, live budget fallback or performance admission.'),indent=2)+'\n');print('COMPLETE NEW POLICY MODEL PASS',len(events),metrics['stats'])
