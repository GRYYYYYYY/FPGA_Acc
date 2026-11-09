"""Reconcile completed whole-cohort/stage evidence; keep every research gate open."""
import copy, hashlib, json, time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'work/current_research_claim_matrix_v21_20261020'
p.mkdir()
def sha(file):
 h=hashlib.sha256()
 with Path(file).open('rb') as stream:
  for b in iter(lambda:stream.read(1048576),b''):h.update(b)
 return h.hexdigest()
old=R/'work/current_research_claim_matrix_v20_20261020/matrix.json'
m=json.loads(old.read_text())
for name,digest in m['source_sha256'].items():assert sha(R/name)==digest,name
plan=R/'experiments/research_plan.json';raw=plan.read_bytes();d=json.loads(raw)
(p/'plan_snapshot.json').write_bytes(raw)
for claim in m['claims']:
 if claim['id']=='H4':
  claim['claim']='Aggregate-port forward and reverse estimators synthesize but their recorded cosimulation fails before RTL'
  claim['limits']='CPU snapshot and exact RR-cost comparisons remain scoped evidence. Aggregate-port C-vector failures precede RTL, and external heap scheduling remains costly. Separate scalar upstream fixture RTL evidence is H5; neither claim establishes representative throughput, integrated timing or physical performance.'
new=[
 dict(id='Q11',gates=['G3','G4'],claim='All five frozen apex2 seeds have verified final joint quality after explicit receipt recovery, with original audit exception preserved',status='supported_in_declared_scope',evidence=['work/completed_prospective5_cohort_final_review_20261020/audit.json','work/prospective_apex2_seeds6_10_summary_queue_20261020/audit.json','work/prospective_receipt_reconciled_cohort_queue_20261020/reconciliation_audit.json','work/prospective_receipt_reconciled_cohort_queue_20261020/reconciled_cohort_audit.json','work/prospective_receipt_reconciled_cohort_queue_20261020/reconciled_native_identity_audit.json'],limits='Original record remains4/5passes and1missing-receipt audit exception. Additive posthoc seed6 receipt recovery yields5/5 final native quality without rerouting. Same circuit, small printed CPD margins and model crossings; not physical SLL, blind heldout, original15-case replacement, all-gate closure or speedup.'),
 dict(id='R3',gates=['G1','G2','G6'],claim='All39536 real estimator snapshot jobs and40 native parent artifacts pass independent correctness replay',status='supported_in_declared_scope',evidence=['work/resident_estimator_complete_replay_review_20261020/audit.json'],limits='19768forward and19768reverse jobs plus19768 decisions. Forward is actual HLS-source C model; reverse CPU model, not full RTL or XRT. Parent-only seed6 CPD failure retained and later refinement remains necessary. No throughput or full authority protocol evidence.'),
 dict(id='H5',gates=['G6'],claim='Scalar upstream ABI passes four fixture Verilog calls including declared rejection controls',status='supported_in_declared_scope',evidence=['work/resident_upstream_word_HLS_20261020/independent_RTL_audit.json'],limits='Fixture csim/csynth/cosim correctness only; aggregate-port failures retained. No representative whole-workload RTL throughput, reverse RTL equivalence, integrated XO/routed clock or physical-card execution.'),
 dict(id='P4',gates=['G2','G7'],claim='Complete initial-sweep CPU bottlenecks and cached/persistent native optimization are verified without changing recorded decisions',status='supported_in_declared_scope',evidence=['work/first_full_policy_cost_analysis_20261020/audit.json','work/initial_sweep_profile_independent_review_20261020/audit.json','work/cached_writer_complete_stage_independent_review_20261020/audit.json','work/persistent_native_route_independent_review_v2_20261020/audit.json','work/persistent_native_full_sweep_review_20261020/audit.json','work/native_session_sweep_auditor_20261020/independent_audit.json','work/optimized_repeat0_initial_complete_review_20261020/audit.json'],limits='Instrumented full sweep4426.197s: native62.80%,writer25.69%,residual11.51%. Cache-only3479.268s and cache/session808.139s are single unpaired loaded-host stage observations. Integrated repeat0 sweep+refresh878.412s matches856+17 decisions and300 observation sets, but CPD remains11.33vs11.1843 and later modes required. No complete-policy or physical FPGA speedup; optimized five complete attempts pending.'),
 dict(id='D1',gates=['G1','G3','G4'],claim='All12 additional-circuit preparation outcomes are audited, with9 exact full-graph native roundtrips and3 baseline failures retained',status='supported_in_declared_scope',evidence=['work/additional_circuit_baseline_independent_review_20261020/audit.json','work/additional_circuit_roundtrip_independent_review_20261020/audit.json','work/additional_circuit_complete_roundtrip_binding_20261020/audit.json','work/additional_circuit_native_cost_independent_review_20261020/audit.json'],limits='misex3,seq,s298,des seeds1-3 at fixed27x22/3layers/width80. All3des packing failures due501IOvs420available retained. 14605002node and25967790edge records sum9attempts, not independent topologies. Native indexed quantization remains rounded ps, not complete VPR objective/RC equivalence. Candidate complete-policy results pending; workspace exposure not audited, no blind-heldout or performance claim.')]
assert not set(c['id'] for c in new)&set(c['id'] for c in m['claims'])
m['claims'].extend(new)
for claim in new:
 for name in claim['evidence']:m['source_sha256'][name]=sha(R/name)
for f in [old,Path(__file__).resolve()]:m['source_sha256'][str(f.relative_to(R))]=sha(f)
m.update(recorded_ns=time.time_ns(),gates=copy.deepcopy([{'id':g['id'],'requirement':g['requirement'],'status':g['status']} for g in d['gates']]),predecessor={'path':str(old.relative_to(R)),'sha256':sha(old)},scope='Thirty scoped claims reconciled after completed five-seed quality/native identity, exact full-parent replay, scalar fixture RTL, full CPU-stage profiling/optimization and all12 additional-circuit preparation outcomes. Every original negative/error remains. All8research gates open; no full-research, blind-heldout, complete-policy speedup or physical-board performance claim.',research_complete=False,board_result=False)
assert len(m['claims'])==30 and len(m['gates'])==8 and all(g['status']!='complete' for g in m['gates'])
m['archived_inputs_sha256'][str((p/'plan_snapshot.json').relative_to(R))]=sha(p/'plan_snapshot.json')
file=p/'matrix.json';file.write_text(json.dumps(m,indent=2)+'\n')
assert plan.read_bytes()==raw
d['current_claim_matrix']={'path':str(file.relative_to(R)),'sha256':sha(file),'status':'partial_current_claims_and_open_gates_reconciled','research_complete':False}
d['prospective_apex2_seeds6_10']['completed_five_seed_final_review']={'audit':'work/completed_prospective5_cohort_final_review_20261020/audit.json','sha256':sha(R/'work/completed_prospective5_cohort_final_review_20261020/audit.json'),'original_joint_passes':4,'original_audit_exceptions':1,'recovered_final_native_quality_passes':5,'planned':5,'scope':'Original missing-receipt exception retained; supplemental posthoc recovery only. Same circuit quality, no physical SLL or independent-circuit generalization.'}
temp=plan.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');temp.replace(plan)
(p/'reconciliation_review.json').write_text(json.dumps({'status':'all30_claims_and_direct_terminal_evidence_reconciled','claims':30,'direct_sources':len(m['source_sha256']),'open_gates':8,'matrix_sha256':sha(file),'research_complete':False},indent=2)+'\n')
print(json.dumps({'claims':30,'direct_sources':len(m['source_sha256']),'open_gates':8}))
