"""Independent complete cold/warm/reference model-state/event/seed parity."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_owned_static_context_two_calls_v1_2026-10-10';vp=D/'verification.json';v=json.loads(vp.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());protocol=json.loads((D/'protocol.json').read_text());assert all(sha(k)==h for k,h in protocol['bindings'].items());old=R/'tools/run_resident_actual_old_linear_undo_model_v13.py';new=R/'tools/run_resident_owned_static_context_model_v1.py';assert ast.dump(ast.parse(new.read_text().replace('from owned_static_rr_context_v1 import load_endpoints','from class_cached_rc_endpoint_context_v1 import load_endpoints')))==ast.dump(ast.parse(old.read_text()));reference=R/'experiments/sha_compact_json_complete_model_pair_v1_2026-10-10/original';refproof=reference.parent/'independent_verification.json';r=json.loads(refproof.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings={str(x):sha(x) for x in [Path(__file__).resolve(),vp,D/'protocol.json',old,new,refproof]};arms=[D/'cold_context',D/'warm_context'];events=None
for arm in arms:
 for rel in ['model/initial.json','model/sketch.json','model/round0.json','model/round1.json','native/subset.json','native/bindings.json']:
  p=arm/rel;ref=reference/rel;x=json.loads(p.read_text());assert x==json.loads(ref.read_text()),(arm.name,rel)
  if rel.startswith('model/'):assert len(x['records'])==len({r['connection_id'] for r in x['records']})==6273
  bindings.update({str(p):sha(p),str(ref):sha(ref)})
 for rel in ['handoff/receipt.json','model/receipt.json','model/shared_audit_receipt.json']:
  p=arm/rel;proof=json.loads(p.read_text())
  for section in ['bindings','files']:assert all(sha(k)==h for k,h in proof.get(section,{}).items())
  bindings[str(p)]=sha(p)
 assert proof['all_three_complete_audits_pass'] and proof['fresh_independent_graph_context'] and proof['diagnostics']['independent_xml_parses']==2
 for rel in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=arm/'model'/rel;proof=json.loads(p.read_text());assert all(sha(k)==h for k,h in proof['bindings'].items());assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings[str(p)]=sha(p)
 assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and proof['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
 a=json.loads((arm/'model/receipt.json').read_text());b=json.loads((reference/'model/receipt.json').read_text());assert len(a['rounds'])==len(b['rounds'])==2;count=0
 for x,y in zip(a['rounds'],b['rounds']):
  assert x.keys()==y.keys();assert {k:v for k,v in x.items() if k not in ['seconds','state_file']}=={k:v for k,v in y.items() if k not in ['seconds','state_file']};count+=len(x['events'])
 events=count;assert (arm/'native/seed.route').read_bytes()==(reference/'native/seed.route').read_bytes();bindings[str(arm/'native/seed.route')]=sha(arm/'native/seed.route')
assert [x['context']['loads'] for x in v['rows']]==[1,1] and [x['context']['accesses'] for x in v['rows']]==[1,2];assert all(sha(k)==h for k,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_queries_states_and_handoff_equal_original_reference=True,all_feedback_events_equal_original_reference=events,all_three_full_independent_audits_both_calls_pass=True,source_AST_only_context_import_changed=True,context_loads_once_current_queries_refreshed=True,rows=v['rows'],scope='Complete same-input two-call component validation against original full reference, including allstates/5048events/seedbytes. Warm cost does not include unpaid cold load: cold cost separately retained. No actual placement/endpoint transaction or complete native/canonical/heldout/hardware gain.'),indent=2)+'\n');print('INDEPENDENT FULL REFERENCE PARITY',events)
