"""Current complete MMC model/wire/native/ignored evidence, scoped clocks only."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10';M=O/'model';N=O/'native';H=O/'handoff';bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')}
def load(p):
 v=json.loads(p.read_text());bindings[str(p)]=sha(p);return v
for p in [O/'initial_parity_verification.json',M/'shared_audit_receipt.json',O/'wire_transaction_verification.json',O/'width_dispatch_verification.json',O/'postchecks/verification.json',O/'canonical/ignored_pin_verification_v1.json',R/'experiments/native_manifest_scope_source_contract_v1_2026-10-10/verification.json']:
 v=load(p);assert all(sha(q)==h for q,h in v['bindings'].items()),str(p);bindings.update(v['bindings'])
initial=load(M/'initial.json');final=load(M/'sketch.json');r=load(M/'receipt.json');h=load(H/'receipt.json');s=load(N/'service_receipt.json');audit=load(M/'verification.json');post=load(O/'postchecks/verification.json');ignored=load(O/'canonical/ignored_pin_verification_v1.json')
for v in [r,h,s]:
 for section in ['bindings','files']:assert all(sha(p)==x for p,x in v[section].items());bindings.update(v[section])
assert initial['required_connections']==initial['completed_connections']==final['required_connections']==final['completed_connections']==115572
assert len(initial['records'])==len(final['records'])==115572 and set(q['connection_id'] for q in initial['records'])==set(q['connection_id'] for q in final['records'])
assert len(r['rounds'])==2 and [len(x['events']) for x in r['rounds']]==[55300,33176]
events=[e for x in r['rounds'] for e in x['events']];statuses=Counter(e['status'] for e in events);fallback=[e for e in events if 'fallback' in e];assert len(events)==88476 and statuses['COMMITTED']==66574 and len(fallback)==137
assert audit['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and audit['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and audit['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
assert s['exit_code']==0 and s['seed_imported'] and len(s['calls'])==143776 and sum(c['connections'] for c in s['calls'])==323680
assert h['selected_connections']==61886 and h['pending_connections']==53686 and h['required_connections']==115572
assert post['all115572_native_physical_queries_and_full_XML_capacity_pass'] and post['native_FULL_and_canonical_semantic_pass'] and post['explicit_ignored_pin_audit_pass']
assert len(ignored['rows'])==1 and ignored['rows'][0]['every_mismatch_matches_native_ignored_sink_pin'] and ignored['rows'][0]['post_reload_packed_netlist_byte_identical'];assert ignored['rows'][0]['mismatch_pin_occurrences']==330 and ignored['rows'][0]['already_correct_ignored_pins']==71 and ignored['rows'][0]['strict_zero_counter_gate_pass'] is False
log=(N/'native.log').read_text();assert 'Completed routing consistency check successfully.' in log and 'NET-aware seed imported' in log and 'VPR succeeded' in log
result=dict(bindings=bindings,complete_current_MMC_initial_floors_paths_epochs_prices_ledgers_events_and_seed_native_pass=True,all_current_native_and_canonical_and_explicit401_ignored_pin_audits_pass=True,strict_zero_native_mapping_counter_gate=False,connections=115572,transactions=len(events),statuses=dict(statuses),live_primary_budget_fallback_calls=len(fallback),fallback_statuses=dict(Counter(e['fallback']['status'] for e in fallback)),estimate_overflow=[initial['overflow_units'],*[x['overflow_after'] for x in r['rounds']]],selected=61886,pending=53686,wirelength=post['wirelength'],diagnostic_cpd_ns=post['diagnostic_cpd_ns'],local_handoff_pipeline_seconds=h['continuous_local_pipeline_seconds'],native_resume_to_finish_seconds=s['seed_resume_to_finish_seconds'],post_native_physical_seconds=post['physical_seconds'],post_canonical_seconds=post['canonical_seconds'],scope='Single exposed MMC frozen RR/placement fresh full endogenous guard model, complete live requests and audits, same-resident audited seed import/native route. Local handoff timer includes model/serialization/full model audits/native; post checks separately scoped. No summing nested clocks, fresh cold arm/input acquisition/fullworkflow netgain, robust timing/functional equivalence/heldout/real-board evidence. Strict zero mapping counter remains false; all330 repaired and71 untouched ignored pins explicitly checked.')
assert all(sha(q)==x for q,x in bindings.items());(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ['bindings','scope']})
