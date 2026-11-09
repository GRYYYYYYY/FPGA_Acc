"""Authenticate both continuous arms, all cases and complete scientific gates."""
import json,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10'
def load(path):return json.loads(path.read_text())
def auth(data):
 for section in ['bindings','files']:
  for path,digest in data.get(section,{}).items():assert sha(path)==digest,(path,section)
r=load(D/'receipt.json');p=load(D/'protocol.json');auth(r);auth(p)
assert r['files'][str(D/'stages.json')]==sha(D/'stages.json')
assert p['optimization']=='namespace-aware Expat v3 complete native and canonical branch audit scans; indexed actual-old budgets and exact undo-stack fallback; hybrid singleton balanced bidirectional v2 and multi-target forward radix, indexed native name membership v2 and seed serializer v2, canonical pin index v2 in both arms; complete audits retained; actual-old linear fallback event audit v9 and frame audit v4 with exact immutable Fraction electrical caching use complete direct readonly XML-array unique-pair RC lattice scans and authenticated channel spans; current-arm resident graph handoff with model and native seed selection/serialization in one subprocess, complete validations retained; two independent XML readers loaded once per current-arm audit subprocess, unchanged complete frame and actual-old fallback event audit bodies'
assert p['cases']==['sha1'] and [x['arm'] for x in r['rows']]==['cold','seed'] and all(x['status']=='COMPLETE_VERIFIED' and x['continuous_arm_seconds']>0 for x in r['rows'])
bindings={str(D/'stages.json'):sha(D/'stages.json'),str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))};cases=[]
for name in p['cases']:
 arms={}
 for mode in p['arm_order']:
  b=D/mode;rr=b/'rr'/name;front=b/'demand'/name;native=b/'native'/name;canonical=b/'canonical'
  proofs=[rr/'verification.json',front/'verification.json',native/'verification.json',canonical/'ignored_pin_verification_v1.json']
  for path in proofs:
   proof=load(path);auth(proof);bindings[str(path)]=sha(path)
  assert load(rr/'verification.json')['complete_manifest_query_partition_and_original_XML_node_type_class_capacity_bbox_pass']
  assert load(front/'verification.json')['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass']
  physical=load(native/'verification.json');assert physical['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and physical['original_native_FULL_check_pass'] and physical['overflow_units']==0
  cp=load(canonical/'receipt.json');cr=next(x for x in cp['rows'] if x['name']==name);assert cr['status']=='SEMANTIC_CANONICAL_PASS' and cr['canonical']['semantic_consistency_gate_pass'];auth(cr['canonical']);bindings[str(canonical/'receipt.json')]=sha(canonical/'receipt.json')
  ip=next(x for x in load(proofs[-1])['rows'] if x['name']==name);assert ip['every_mismatch_matches_native_ignored_sink_pin'] and ip['post_reload_packed_netlist_byte_identical']
  receipt=load(native/'receipt.json');auth(receipt);bindings[str(native/'receipt.json')]=sha(native/'receipt.json');required=len(load(front/'endpoints.json')['connections']);assert required==6273 and physical['physical_connections']==required
  if mode=='seed':
   model=b/'model'/name
   for f in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
    path=model/f;proof=load(path);auth(proof);bindings[str(path)]=sha(path)
    assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
   assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and proof['completed']==required
   assert proof['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
   shared_path=model/'shared_audit_receipt.json';shared=load(shared_path);auth(shared);bindings[str(shared_path)]=sha(shared_path)
   assert shared['all_three_complete_audits_pass'] and shared['complete_audit_bodies_AST_preserved'] and shared['fresh_independent_graph_context']
   cs=shared['cache_diagnostics'];assert cs['contexts']==1 and cs['hits']>0 and cs['entries']==cs['misses']>0 and cs['calls']==cs['hits']+cs['misses']
   assert shared['diagnostics']['contexts']==shared['diagnostics']['context_loads']==1 and shared['diagnostics']['accesses']==3 and shared['diagnostics']['independent_xml_parses']==2
   assert [x['audit'] for x in shared['stages']]==['initial_physical_verification.json','sketch_physical_verification.json','verification.json']
   model_receipt=load(model/'receipt.json');auth(model_receipt);bindings[str(model/'receipt.json')]=sha(model/'receipt.json');model_events=[e for row in model_receipt['rounds'] for e in row['events']];assert len(model_receipt['rounds'])==2 and proof['events']==len(model_events) and proof['committed']==sum(e['status']=='COMMITTED' for e in model_events) and proof['retained']==sum(e['status']=='RETAIN_BUDGET_OR_UNREACHABLE' for e in model_events)
   handoff_path=b/'handoff'/name/'receipt.json';handoff=load(handoff_path);auth(handoff);bindings[str(handoff_path)]=sha(handoff_path)
   assert handoff['required_connections']==required and handoff['selected_connections']+handoff['pending_connections']==required
   subset=load(native/'subset.json');assert len(subset['records'])==handoff['selected_connections'] and len(subset['pending'])==handoff['pending_connections'] and len(subset['records'])+len(subset['pending'])==required
   assert (native/'seed.route').is_file()
  else:assert not (native/'seed.route').exists() and not (b/'model').exists()
  arms[mode]=dict(required=required,rr_sha256=sha(rr/'rr_graph.xml'),input_sha256={f:sha(rr/f) for f in ['design.blif','design.net','design.place']},command=receipt['command'],native_seconds=receipt['native_process_seconds'],iterations=physical['iterations'],wirelength=receipt['wirelength'],diagnostic_cpd_ns=receipt['diagnostic_cpd_ns'])
 moved=R/'experiments/sha_second_legal_swap_endpoints_v1_2026-10-10/sha1'
 for mode in ['cold','seed']:
  for filename in ['design.blif','design.net','design.place']:
   assert (D/mode/'rr'/name/filename).read_bytes()==(moved/filename).read_bytes()
 c,s=arms['cold'],arms['seed'];assert c['required']==s['required'] and c['rr_sha256']==s['rr_sha256'] and c['input_sha256']==s['input_sha256']
 def normalize(cmd):
  cmd=cmd.copy();cmd[cmd.index('--read_rr_graph')+1]='FRESH_MATCHED_GRAPH';return cmd
 assert normalize(c['command'])==normalize(s['command'])
 cases.append(dict(name=name,arms=arms))
frozen=R/'experiments/sha_whole_net_initial_cache_sequence_v1_2026-10-10'
fp=frozen/'independent_verification.json';fproof=load(fp);auth(fproof);assert fproof['all6273_records_allstates_match_current_endpoint'] and fproof['all3_complete_independent_audits_each_phase_pass'];bindings[str(fp)]=sha(fp)
for filename in ['initial.json','sketch.json','round0.json','round1.json']:
 fresh=D/'seed/model/sha1'/filename;prior=frozen/'new_warm_context/model'/filename
 assert load(fresh)==load(prior);bindings[str(prior)]=sha(prior)
assert (D/'seed/native/sha1/seed.route').read_bytes()==(frozen/'new_warm_context/native/seed.route').read_bytes()
native_qor_gate=all(c['arms']['seed']['wirelength']<=c['arms']['cold']['wirelength'] and c['arms']['seed']['diagnostic_cpd_ns']<=c['arms']['cold']['diagnostic_cpd_ns'] for c in cases)
ct,st=[x['continuous_arm_seconds'] for x in r['rows']];assert all(sha(k)==v for k,v in bindings.items())
result=dict(bindings=bindings,all_cases_both_complete_arms_authenticated=True,matched_printed_native_qor_nonregression_gate=native_qor_gate,cases=cases,cold_continuous_cohort_seconds=ct,seed_continuous_cohort_seconds=st,seed_over_cold_ratio=st/ct,observed_single_trial_continuous_time_gain=st<ct,observed_single_trial_joint_time_and_printed_native_qor_gate=st<ct and native_qor_gate,scope='Full single SHA frozen fixed-placement harness; single cold-then-seed wall timer reported by producer code, not independently reconstructed from per-stage clocks. RR XML and fixed input bytes equal across fresh arms. Validation included. No fastest conventional cold/replicate stability/HDL/real async timing/strict-heldout/silicon proof. Nonzero ignored-pin counters remain explicit.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','cases']},indent=2))
