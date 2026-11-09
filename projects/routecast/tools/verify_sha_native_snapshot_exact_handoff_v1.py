"""Full guarded model equivalence from native snapshot/decimal metadata to original full XML rebuild."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_native_snapshot_exact_handoff_v1_2026-10-10';A=D/'model';B=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/model/sha1';bindings={str(Path(__file__)):sha(Path(__file__))};events=0
for rel in ['native_resident_csr_order_v2_2026-10-10/verification.json','native_switch_exact_rc_boundary_v1_2026-10-10/verification.json','native_switch_exact_rc_boundary_v1_2026-10-10/exact_switch_metadata.json','sha_native_resident_snapshot_v4_2026-10-10/independent_verification.json']:
 p=R/'experiments'/rel;v=json.loads(p.read_text())
 for section in ['bindings','files']:assert all(sha(q)==h for q,h in v.get(section,{}).items())
 bindings[str(p)]=sha(p)
for W in [A,B]:
 for name in ['receipt.json','protocol.json','shared_audit_receipt.json','initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=W/name;v=json.loads(p.read_text())
  for section in ['bindings','files']:assert all(sha(q)==h for q,h in v.get(section,{}).items())
  bindings[str(p)]=sha(p)
  if name=='shared_audit_receipt.json':assert v['all_three_complete_audits_pass'] and v['fresh_independent_graph_context']
  if name=='verification.json':assert v['complete_prospective_overflow_guard_rejected_candidate_and_unchanged_epoch_pass'] and v['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
for name in ['initial.json','floors.json','sketch.json','round0.json','round1.json']:
 p=A/name;q=B/name;v=json.loads(p.read_text());assert v==json.loads(q.read_text())
 if name!='floors.json':assert len(v['records'])==6273
 bindings.update({str(p):sha(p),str(q):sha(q)})
x=json.loads((A/'receipt.json').read_text());y=json.loads((B/'receipt.json').read_text());assert len(x['rounds'])==len(y['rounds'])==2
for a,b in zip(x['rounds'],y['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']};events+=len(a['events'])
p=R/'tools/run_resident_native_snapshot_exact_guard_model_v2.py';q=R/'tools/run_resident_overflow_guard_model_v1.py';s=p.read_text().replace('from native_snapshot_exact_context_v2 import load_endpoints','from class_cached_rc_endpoint_context_v1 import load_endpoints');assert ast.dump(ast.parse(s))==ast.dump(ast.parse(q.read_text()));bindings.update({str(p):sha(p),str(q):sha(q)});N=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/native/sha1'
for filename in ['subset.json','bindings.json']:
 p=D/'native'/filename;q=N/filename;assert json.loads(p.read_text())==json.loads(q.read_text());bindings.update({str(p):sha(p),str(q):sha(q)})
p=D/'native/seed.route';q=N/'seed.route';assert p.read_bytes()==q.read_bytes();bindings.update({str(p):sha(p),str(q):sha(q)})
for p in [D/'receipt.json',D/'protocol.json',D/'handoff/receipt.json']:
 v=json.loads(p.read_text())
 for section in ['bindings','files']:assert all(sha(q)==h for q,h in v.get(section,{}).items())
 bindings[str(p)]=sha(p)
p=R/'tools/run_sha_native_snapshot_exact_guard_handoff_v1.py';q=R/'tools/run_sha_overflow_guard_native_handoff_v1.py';s=p.read_text().replace('from run_resident_native_snapshot_exact_guard_model_v2 import predict','from run_resident_overflow_guard_model_v1 import predict');assert ast.dump(ast.parse(s))==ast.dump(ast.parse(q.read_text()));bindings.update({str(p):sha(p),str(q):sha(q)})
assert all(sha(p)==h for p,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_full_states_floors_and_rejected_candidates_equal_original=True,all_events_equal=events,whole_model_AST_equal_except_context_import=True,full3_fresh_original_XML_audits_pass=True,whole_NET_subset_pin_bindings_and_seed_bytes_equal_original=True,scope='Snapshot serialization/verification acquisition paid separately; Native node PTC and full current seed serialization certified; no inprocess predictor/zero-copy/fulltime gain.'),indent=2)+'\n');print('FULL NATIVE SNAPSHOT EXACT MODEL PARITY',events)
