"""Evidence-scoped claim inventory; no gate or research completion certification."""
from pathlib import Path
import hashlib,json,time
R=Path(__file__).resolve().parents[1]
def main():
 refs={};snapshots={}
 def read(relative):
  f=R/relative;raw=f.read_bytes();refs[relative]=hashlib.sha256(raw).hexdigest();snapshots[relative]=raw;return json.loads(raw)
 quality=read('work/native_refreshed_critical_policy_v1_20261016/independent_audit.json')
 repeat=read('work/native_instrumented_compound_repeat_review_20261016/independent_audit.json')
 timing=read('work/native_instrumented_compound_timing_review_20261016/audit.json')
 migration=read('work/three_layer_migration_native_pair_review_20261016/independent_audit.json')
 xo=read('work/lean_start_actual_XO_comparison_20261017/audit.json')
 rtl=read('work/native_start_validate_only_RTL_20261017/independent_audit.json')
 failure=read('work/integrated_control_route_failure_terminal_20261016/audit.json')
 random=read('work/implicit_tree_budget_checks_20261017/audit.json')
 oracle=read('work/implicit_tree_budget_oracle_checks_20261017/audit.json')
 probe=read('work/implicit_native_tree_probe_20261017/audit.json')
 reserved=read('experiments/reserved_validation_protocol_20261017.json')
 plan=read('experiments/research_plan.json')
 assert len(quality['outcomes'])==3 and all(v['joint_baseline_pass'] for v in quality['outcomes'])
 assert len(repeat['comparisons'])==3 and all(v['final_tree_identical'] and v['quality_identical'] for v in repeat['comparisons'])
 assert len(timing['cases'])==3
 assert all(len(v)==5 and not any(r['joint_baseline_pass'] for r in v) for v in migration['outcomes'].values())
 assert rtl['RTL_calls']==75 and xo['resource_delta']['LUT']==-34215
 assert failure['link_returncode']==1 and random['comparisons']==7200 and oracle['random_graphs']==400
 def claim(id,gates,text,status,evidence,limit,measurements=None):
  return dict(id=id,gates=gates,claim=text,status=status,evidence=evidence,limits=limit,measurements=measurements)
 claims=[
 claim('Q1',['G4'],'Joint baseline nondegradation on three development cases','supported_in_declared_scope',['work/native_refreshed_critical_policy_v1_20261016/independent_audit.json'],'CPU refinement with shared binder and native STA; ex5p margin0.5ps; neither heldout nor FPGA.',quality['outcomes']),
 claim('Q2',['G2','G4'],'Same-configuration full execution reproduces final trees and quality','supported_in_declared_scope',['work/native_instrumented_compound_repeat_review_20261016/independent_audit.json'],'One independent repeat; not multiple seeds or confidence intervals.',repeat['comparisons']),
 claim('P1',['G4','G7'],'Full refinement pipeline establishes acceleration','not_supported',['work/native_instrumented_compound_timing_review_20261016/audit.json'],'High CPU costs; includes explicit verification, source preflight excluded; no physical-board comparison.',{r['case']:r['full_case_wall_ns']/1e9 for r in timing['cases']}),
 claim('M1',['G5'],'Adaptive placement improves end-to-end performance and quality','not_supported',['work/three_layer_migration_native_pair_review_20261016/independent_audit.json'],'Backpressure decreases but remote reads and mean wall time increase; both quality gates fail.',{arm:dict(backpressure=rows[0]['backpressure'],remote_reads=rows[0]['remote_shadow_reads'],mean_full_seconds=sum(r['full_run_wall_ns'] for r in rows)/5e9) for arm,rows in migration['outcomes'].items()}),
 claim('H1',['G6'],'Validation-only start split preserves fixture RTL behavior and reduces actual XO synthesis estimates','supported_in_declared_scope',['work/lean_start_actual_XO_comparison_20261017/audit.json','work/native_start_validate_only_RTL_20261017/independent_audit.json'],'75 fixture RTL calls; actual XO ABI/source and estimated area checked; not routed resources or timing.',xo['resource_delta']),
 claim('H2',['G6'],'Current integrated design meets legal routing and300MHz signoff','pending',['work/integrated_control_route_failure_terminal_20261016/audit.json'],'Previous link failed illegal routing; successor implementation still running. Link success alone insufficient.'),
 claim('I1',['G4'],'Implicit filtering preserves tested search behavior with lower local CPU cost','supported_in_declared_scope',['work/implicit_tree_budget_checks_20261017/audit.json','work/implicit_tree_budget_oracle_checks_20261017/audit.json','work/implicit_native_tree_probe_20261017/audit.json'],'Random differential and per-step exhaustive smallgraph oracles; one native first-net snapshot. OriginalCSR edge indices differ by design. Fullpipeline outcomes pending.',probe['outcomes']),
 claim('V1',['G3','G4'],'Reserved validation establishes generalization','pending',['experiments/reserved_validation_protocol_20261017.json'],'Protocol only; reserved inputs unopened, no measurements.'),
 claim('B1',['G7'],'Physical-board end-to-end3x and energy targets achieved','not_established',[],'Physical card unavailable in recorded environment; neither CPU nor emulation substitutes for board measurements.'),
 ]
 for c in claims:
  assert all(e in refs for e in c['evidence'])
 gates=[dict(id=g['id'],requirement=g['requirement'],status=g['status'],completion_proven=False,reason='Evidence is partial; plan requirements retain their original scope.') for g in plan['gates']]
 for directory,pid in [('native_start_validate_only_hw_20261017',958046),('native_adaptive_compound_integration_v2_20261017',928257),('native_implicit_compound_repeat_v2_20261017',1189517)]:
  f=Path('/proc')/str(pid)/'stat';assert f.exists(),('refresh terminal state before exporting',directory)
  raw=f.read_text();refs['/proc/'+str(pid)+'/stat_snapshot']=hashlib.sha256(raw.encode()).hexdigest()
 O=R/'work/current_research_claim_matrix_v2_20261017';O.mkdir(exist_ok=False)
 script=Path(__file__);refs[str(script.relative_to(R))]=hashlib.sha256(script.read_bytes()).hexdigest()
 report=dict(schema='dieroute.claim_matrix.v2',status='partial_current_claims_and_open_gates_reconciled',recorded_ns=time.time_ns(),claims=claims,gates=gates,source_sha256={k:v for k,v in refs.items() if not k.startswith('/proc/')},scope='Direct finalized audit records bound by hash; original solver proofs are not rerun here. Pending jobs freshly observed live. No gate completion certification; no claim of comprehensive novelty review.',research_complete=False,board_result=False)
 for relative,raw in snapshots.items():
  destination=O/'inputs'/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
 report['archived_inputs_sha256']={str((O/'inputs'/relative).relative_to(R)):hashlib.sha256(raw).hexdigest() for relative,raw in snapshots.items()}
 (O/'matrix.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],claims=len(claims),open_gates=len(gates))))
if __name__=='__main__':main()
