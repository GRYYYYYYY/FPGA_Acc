"""Independent full paired state/event/seed and source-format-only verification."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_compact_json_complete_model_pair_v1_2026-10-10';p=D/'verification.json';v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());protocol=json.loads((D/'protocol.json').read_text());assert all(sha(k)==h for k,h in protocol['bindings'].items());assert [x['arm'] for x in v['rows']]==['original','compact'] and all(x['exit_codes']==[0,0] for x in v['rows']);old=R/'tools/run_resident_actual_old_linear_undo_model_v13.py';new=R/'tools/run_resident_actual_old_linear_undo_model_compact_json_v1.py';assert ast.dump(ast.parse(new.read_text().replace(',indent=None)',',indent=2)')))==ast.dump(ast.parse(old.read_text()));A=D/'original';B=D/'compact';bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,D/'protocol.json',old,new]};comparisons=[]
for rel in ['model/initial.json','model/sketch.json','model/round0.json','model/round1.json','native/subset.json','native/bindings.json']:
 a=A/rel;b=B/rel;x=json.loads(a.read_text());y=json.loads(b.read_text());assert x==y
 if rel.startswith('model/'):
  assert len(x['records'])==len({r['connection_id'] for r in x['records']})==6273
 bindings.update({str(a):sha(a),str(b):sha(b)});comparisons.append(rel)
receipts=[]
for arm in [A,B]:
 for rel in ['handoff/receipt.json','model/receipt.json','model/shared_audit_receipt.json']:
  pp=arm/rel;r=json.loads(pp.read_text())
  for section in ['bindings','files']:assert all(sha(k)==h for k,h in r.get(section,{}).items())
  bindings[str(pp)]=sha(pp)
 assert r['all_three_complete_audits_pass'] and r['fresh_independent_graph_context'] and r['diagnostics']['independent_xml_parses']==2
 for filename in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  pp=arm/'model'/filename;proof=json.loads(pp.read_text());assert all(sha(k)==h for k,h in proof['bindings'].items());assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings[str(pp)]=sha(pp)
 assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and proof['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
 receipts.append(json.loads((arm/'model/receipt.json').read_text()))
assert receipts[0].keys()==receipts[1].keys();events=0
for x,y in zip(receipts[0]['rounds'],receipts[1]['rounds']):
 assert x.keys()==y.keys();assert {k:v for k,v in x.items() if k not in ['seconds','state_file']}=={k:v for k,v in y.items() if k not in ['seconds','state_file']};events+=len(x['events'])
assert len(receipts[0]['rounds'])==len(receipts[1]['rounds'])==2
for rel in ['model/protocol.json']:
 x=json.loads((A/rel).read_text());y=json.loads((B/rel).read_text());assert x.keys()==y.keys() and {k:v for k,v in x.items() if k!='bindings'}=={k:v for k,v in y.items() if k!='bindings'}
assert (A/'native/seed.route').read_bytes()==(B/'native/seed.route').read_bytes()
for pp in [A/'native/seed.route',B/'native/seed.route']:bindings[str(pp)]=sha(pp)
assert all(sha(k)==h for k,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_records_each_state_equal=True,all_round_events_equal=events,source_AST_format_only=True,complete_model_protocol_scientific_fields_equal=True,all_three_audits_each_arm_pass=True,seed_bytes_identical=True,local_paired_seconds=v['rows'],receipt_byte_sizes={arm.name:(arm/'model/receipt.json').stat().st_size for arm in [A,B]},scope='Independent full states/5048events/seed/complete audits/source-format-only parity. Source/timing/outputpath bindings metadata differ and are individually authenticated, no omitted scientific fields. Single local paired model/handoff/audit timings, not full native/canonical workflow/heldout/hardware proof.'),indent=2)+'\n');print('INDEPENDENT COMPLETE PARITY',events,[(x['arm'],x['complete_local_model_handoff_audit_seconds']) for x in v['rows']])
