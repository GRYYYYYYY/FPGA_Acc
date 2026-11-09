"""Verify the whole measured provided-route boundary and actual native outputs."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'old_route_native_owner_workflow_v3_2026-10-08';bindings={}
def read(path):
 obj=json.loads(path.read_text())
 for name,digest in obj.get('bindings',{}).items():
  assert sha(name)==digest,name
  assert name not in bindings or bindings[name]==digest
  bindings[name]=digest
 bindings[str(path)]=sha(path)
 return obj
r=read(D/'receipt.json');p=read(D/'protocol.json')
assert sha(D/'protocol.json')==r['protocol_sha256']
assert len(r['stages'])==13 and [s['script'] for s in r['stages']]==p['stages']
assert all(s['exit_code']==0 and s['elapsed_seconds']>0 for s in r['stages'])
total=sum(s['elapsed_seconds'] for s in r['stages'])
assert total<=r['declared_input_workflow_seconds']
for stage in r['stages']:
 path=D/(Path(stage['script']).name+'.log');bindings[str(path)]=sha(path)
candidate=read(E/'raw_route_native_owner_candidate_v3_2026-10-08/verification.json')
for key in ('all8_budget_attempts_and_complete_state_equal','all6_critical_owner_searches_and_blockers_equal',
            'all4_owner_candidates_and102_stage_certificate_contents_equal','all1929_wire_events_answers_work_counts_and_full_state_equal'):
 assert candidate[key]
native=read(E/'native_owner_candidate_reload_v3_2026-10-08/verification.json')
canonical=read(E/'native_owner_candidate_canonical_v3_2026-10-08/verification.json')
quality=read(E/'native_owner_candidate_reload_v3_2026-10-08/native_quality_verification.json')
assert native['connections']==1929 and native['changed_physical_connection_ids']==[]
assert native['pin_mismatches']==2175 and native['trace_fixups']==1624
assert canonical['all1929_paths_and_original_xml_physical_checks_pass']
assert canonical['pin_mismatches']==canonical['trace_fixups']==0
assert quality['full_chain_pass'] and quality['joint_quality_pass']
assert quality['wirelength']==11497 and quality['cpd_ns']=='283577/100000'
assert candidate['original_budget_violation_ids']==native['budget_violation_connection_ids']==canonical['budget_violation_connection_ids']==[785,1637]
assert quality['budget_safe_connections']==1927
entry=read(E/'native_owner_candidate_reload_v3_2026-10-08/entry_verification.json')
assert entry['original_packed_netlist_and_target_place_byte_identity_pass'] and entry['pin_identity_freshly_captured_in_this_directory']
seed=read(E/'fresh_retained_branch_seed_v7_2026-10-08/verification.json')
resume=read(E/'fresh_retained_branch_resume_v7_2026-10-08/parity_verification_v2.json')
assert seed['all1929_retained_release_decisions_and_physical_fraction_witnesses_equal'] and resume['all1929_fresh_resume_physical_paths_equal_historical']
ledger_proof=read(E/'transaction_shared_tree_ledger_v1_2026-10-08/verification.json')
assert ledger_proof['all_four_transaction_trace_reference_counts_parents_capacity_pass'] and ledger_proof['failed_operation_atomicity_cases']==5
boundary=read(E/'native_minrc_certificate_boundaries_v4_retry_2026-10-08/verification.json')
assert boundary['all10_integer_constraints_minima_and_certificate_cases_pass']
assert len(boundary['invalid_domain_rejections'])==10
assert len(boundary['capacity_contract_rejections'])==20
assert all(x['certificate_calls']==x['generic_calls']==1 for x in boundary['normalization_calls'])
bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all_thirteen_measured_stages_terminal_zero=True,
         declared_input_workflow_seconds=r['declared_input_workflow_seconds'],
         stages=r['stages'],residual_seconds=r['declared_input_workflow_seconds']-total,
         cpd_ns=quality['cpd_ns'],wirelength=11497,joint_printed_quality_pass=True,
         budget_safe_connections=1927,original_budget_violation_ids=[785,1637],
         first_native_fixups=1624,canonical_fixups=0,
         full_original_input_workflow_seconds=None,
         scope='One prospective clock includes fresh candidate generation and all thirteen fresh seed/resume/candidate/development verification/native/quality/entry stages and freshly generated original-input identity, subprocesses and outputs. Begins with supplied old accepted route and supplied endpoint/budget/model/original packed netlist and target placement artifacts. Initial protocol and final wrapper receipt/this fee audit excluded. Same-declared-input cold observation measured separately; no paired or full original-input gain proved. Original-input net gain, all-budget admission, original HDL equivalence and unseen-family validity unproved.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
