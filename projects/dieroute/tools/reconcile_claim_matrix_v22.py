"""Add current terminal evidence without closing gates or rewriting frozen matrices."""
from pathlib import Path
import json,hashlib,time,os,copy
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 old=R/'work/current_research_claim_matrix_v21_20261020/matrix.json';m=json.loads(old.read_text())
 drift=[]
 for name,digest in m['source_sha256'].items():
  p=R/name
  if not p.exists() or sha(p)!=digest:drift.append(name)
 assert not drift,drift
 out=R/'work/current_research_claim_matrix_v22_20261021';out.mkdir()
 plan=R/'experiments/research_plan.json';raw=plan.read_bytes();d=json.loads(raw);(out/'plan_snapshot.json').write_bytes(raw)
 specs=[
 ('Q12',['G3','G4'],'All12 additional-circuit terminal outcomes retained:7 joint-quality passes,2 candidate capacity failures,3 baseline packing failures',[
 'work/additional_circuit_terminal_reconciliation_20261021/summary.json','work/additional_circuit_parent_capacity_failure_review_20261021/review.json'],
 'Only4passes have no known launch-receipt exception;3additional native-quality passes retain missing upstream wirelength launch provenance. Baselinelegal denominator9 and original denominator12 both retained. Two failures on baselinelegal inputs contradict no-increased-failure requirement. Fallback restores many baseline nets; not standalone hierarchical quality, blind heldout or physical SLL.'),
 ('P5',['G2','G7'],'Five optimized complete same-input CPU policy attempts reproduce exact parent/final trees and joint quality',[
 'work/persistent_native_full_policy_repeat_audit_queue_20261020/audit.json','work/optimized_policy_acceleration_coverage_budget_20261020/audit.json'],
 'Shared-host descriptive full-attempt durations, prepared-input scope. Not independent circuits, paired statistical speedup, FPGA acceleration or proof all coarse groups can be offloaded. Parent-only infinite acceleration ceiling1.579; native verification remains required.'),
 ('P6',['G2','G7'],'Native private CPU repair preserves the complete856-decision initial sweep and297 native observations',[
 'work/native_private_repair_full_sweep_review_20261020/audit.json','work/native_private_repair_reproducibility_20261020/package_review.json'],
 '610.76388429s is one unpaired loaded-host stage observation including setup. Portable package covers CPU correctness subset only. No full-policy paired speedup, HLS implementation, asynchronous authority proof or board evidence.'),
 ('R4',['G1','G2','G6'],'Ten declared cases and271560 chronological estimator jobs pass trace replay and native parent equality',[
 'work/representative_estimator_independent_review_v2_20261020/audit.json'],
 'Forward HLS-source C model and reverse CPU model. Original quality failure strata retained. Replay correctness is not representative RTL workload throughput, integrated authority correctness or acceleration.'),
 ('H6',['G6'],'Opcode-split H implementation fully routes but fails requested300MHz setup timing',[
 'work/execute_opcode_split_routed_review_20261020/independent_audit.json','work/execute_opcode_split_critical_path_diagnosis_20261021/reported_cone_followup.json'],
 'WNS-2.262ns and61859setup failing endpoints; routing/hold/DRC success does not close setup. Worst reported data path lies in SLR0 with modest local fanout; not evidence all failures have the same cause. No lower-clock substitution or board performance claim.'),
 ('H7',['G6'],'Explicit pipelined entry-bounds predicate has registered generated RTL and passes75fixture Verilog calls with unchanged external ABI',[
 'work/entry_bounds_pipeline_HLS_20261021/RTL_cosim_review.json','work/entry_bounds_pipeline_HLS_20261021/RTL_boundary_review.json','work/entry_bounds_pipeline_HLS_20261021/HLS_estimate_review.json','work/entry_bounds_stage_HLS_20261021/RTL_boundary_review.json'],
 '321145fixture cycles vs H321425. Full64-bit bounds, record checks and overlay semantics preserved in finite tests. First latency-only fork retains completion bypass; explicit pipeline removes it in generated helper only. Actual XO/physical optimization and timing remain unproven; HLS2.433ns estimate is not signoff.')]
 ids={c['id'] for c in m['claims']}
 for ident,gates,claim,ev,limits in specs:
  assert ident not in ids
  m['claims'].append(dict(id=ident,gates=gates,claim=claim,status='supported_in_declared_scope',evidence=ev,limits=limits))
  for name in ev:m['source_sha256'][name]=sha(R/name)
 for c in m['claims']:
  if c['id']=='P4':c['limits']+=' Later completed full repeats and private CPU stage are separately reconciled in P5/P6; earlier pending wording is historical.'
  if c['id']=='D1':c['limits']+=' Complete terminal outcomes supersede pending scope in Q12; original preparation evidence unchanged.'
 gates=[dict(id=g['id'],requirement=g['requirement'],status=g['status']) for g in d['gates']]
 assert len(gates)==8 and all(g['status']!='complete' for g in gates)
 m.update(schema='dieroute.claim_matrix.v22',recorded_ns=time.time_ns(),gates=gates,predecessor=dict(path=str(old.relative_to(R)),sha256=sha(old)),scope='36scoped claims with all12heterogeneous outcomes and all original provenance exceptions/failures retained. Complete CPU repeats, native repair, representative replay and H setup failure reconciled. Pipelined predicate fixture RTL is not physical success. All8original gates remain open.',research_complete=False,board_result=False)
 for p in [old,Path(__file__),out/'plan_snapshot.json']:m['source_sha256'][str(p.relative_to(R))]=sha(p)
 file=out/'matrix.json';file.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 assert plan.read_bytes()==raw
 d['current_claim_matrix']=dict(path=str(file.relative_to(R)),sha256=sha(file),status=m['status'],research_complete=False)
 new=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode();tmp=plan.with_suffix('.matrix22.tmp');tmp.write_bytes(new);assert plan.read_bytes()==raw;os.replace(tmp,plan)
 (out/'reconciliation_review.json').write_text(json.dumps(dict(status='36claims_direct_evidence_hashes_reconciled',claims=len(m['claims']),direct_sources=len(m['source_sha256']),open_gates=8,predecessor_source_drift=drift,matrix_sha256=sha(file),plan_before_sha256=hashlib.sha256(raw).hexdigest(),plan_after_sha256=hashlib.sha256(new).hexdigest(),scope='Direct evidence hashes verified; transitive component audits retain their own coverage limits.',research_complete=False),indent=2)+'\n')
 print(json.dumps(dict(claims=len(m['claims']),sources=len(m['source_sha256']),open_gates=8)))
if __name__=='__main__':main()
