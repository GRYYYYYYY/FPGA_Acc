"""Verify the whole measured provided-route boundary and actual native outputs."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'provided_raw_route_workflow_v1_2026-10-08';bindings={}
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
assert len(r['stages'])==7 and [s['script'] for s in r['stages']]==p['stages']
assert all(s['exit_code']==0 and s['elapsed_seconds']>0 for s in r['stages'])
total=sum(s['elapsed_seconds'] for s in r['stages'])
assert total<=r['provided_route_workflow_seconds']
for stage in r['stages']:
 path=D/(stage['script']+'.log');bindings[str(path)]=sha(path)
candidate=read(E/'raw_route_candidate_pipeline_v4_2026-10-08/verification.json')
for key in ('all8_budget_attempts_and_complete_state_equal','all6_critical_owner_searches_and_blockers_equal',
            'all4_owner_candidates_and102_stage_certificates_equal','all5787_wire_events_answers_work_counts_and_full_states_equal'):
 assert candidate[key]
native=read(E/'raw_candidate_native_reload_v2_2026-10-08/verification.json')
canonical=read(E/'raw_candidate_canonical_v2_2026-10-08/verification.json')
quality=read(E/'raw_candidate_native_reload_v2_2026-10-08/native_quality_verification.json')
assert native['connections']==1929 and native['changed_physical_connection_ids']==[]
assert native['pin_mismatches']==193 and native['trace_fixups']==99
assert canonical['all1929_paths_and_original_xml_physical_checks_pass']
assert canonical['pin_mismatches']==canonical['trace_fixups']==0
assert quality['full_chain_pass'] and quality['joint_quality_pass']
assert quality['wirelength']==11474 and quality['cpd_ns']=='283577/100000'
assert candidate['original_budget_violation_ids']==native['budget_violation_connection_ids']==canonical['budget_violation_connection_ids']==[785,1637]
assert quality['budget_safe_connections']==1927
bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all_seven_measured_stages_terminal_zero=True,
         provided_route_workflow_seconds=r['provided_route_workflow_seconds'],
         stages=r['stages'],residual_seconds=r['provided_route_workflow_seconds']-total,
         cpd_ns=quality['cpd_ns'],wirelength=11474,joint_printed_quality_pass=True,
         budget_safe_connections=1927,original_budget_violation_ids=[785,1637],
         first_native_fixups=99,canonical_fixups=0,
         full_original_input_workflow_seconds=None,
         scope='One prospective clock includes fresh candidate generation and all seven development verification/native/quality stages, subprocesses and outputs. Begins with supplied post-resume route and supplied endpoint/budget/model/identity artifacts. Initial protocol and final wrapper receipt/this fee audit excluded. No symmetric cold same-start workflow measured. Original-input net gain, all-budget admission, original HDL equivalence and unseen-family validity unproved.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
