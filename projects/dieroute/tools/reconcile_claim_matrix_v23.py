"""Reconcile diagnostic and isolated-development evidence without closing gates."""
from pathlib import Path
import json,hashlib,time,os
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 old=R/'work/current_research_claim_matrix_v22_20261021/matrix.json';m=json.loads(old.read_text());drift=[name for name,h in m['source_sha256'].items() if not (R/name).is_file() or sha(R/name)!=h];assert not drift,drift
 out=R/'work/current_research_claim_matrix_v23_20261021';out.mkdir();plan=R/'experiments/research_plan.json';raw=plan.read_bytes();d=json.loads(raw);(out/'plan_snapshot.json').write_bytes(raw)
 specs=[
 ('D2',['G3','G4'],'Retained seq capacity failures localized to one IPIN and two channel nodes on VPR layer1; matched-anchor local capacity reachability differs with layer restrictions',[
 'work/additional_parent_failure_localization_20261021/native_rr_join.json','work/additional_parent_failure_localization_20261021/iteration_trajectory_review.json','work/additional_parent_failure_localization_20261021/sink_predecessor_capacity_review.json','work/additional_parent_failure_localization_20261021/matched_layer_reachability_comparison.json'],
 'Static final-state diagnostic only.52distinct nets share one sink equivalence class with80predecessor capacity and29empty pins. No unique net owner follows from SINK ID. Two free pins reachable only with layer excursions from matched safe layer1 anchors under fixed other-net occupancy; does not exclude coordinated same-layer routing or establish full causal attribution, repair, native timing or physical SLL.'),
 ('D3',['G2','G4'],'Frozen CPU library reproduces a five-node counterexample where a successful conflicting hierarchical path suppresses a conflict-free repeated-layer flat alternative',[
 'work/repeated_layer_corridor_counterexample_20261021/review.json'],
 'Mechanism reproduced on a synthetic graph. Not a complete explanation of original seq failures or proof all repeated-layer paths should be admitted. Original cohort and source unchanged.'),
 ('A1',['G2','G4','G5'],'Isolated conflict-triggered capacity-safe global alternative passes finite controls and2000fixed synthetic differential assertions',[
 'work/conflict_capacity_detour_variant_20261021/review.json','work/conflict_capacity_detour_variant_20261021/random_review.json'],
 'Different algorithm with one extra global search per conflicting hierarchical branch and strict lower-cost replacement.73changed candidates avoid initially full resources;123extra searches,897extra expansions.338unreachable cases retained;2000assertion passes are not2000routes. No native full-policy quality, hardware implementation or acceleration; testing does not prove all inputs, concurrency or publication.'),
 ('A2',['G2','G4','G7'],'Four read-only native-size final-state diagnostic searches return two conflict-free alternatives with higher search work',[
 'work/conflict_detour_native_snapshot_probe_20261021/review.json'],
 'Two nets,original packed criticality but synthetic zero seed depth/cost,source-safe anchors. Not chronological replay,whole-net routing or native timing validation. No authority changes. Approximate doubling in single shared-host query search time is descriptive, not paired full-policy speedup. Separate12case parent-only development protocol launched; no outcomes presumed.'),
 ('E1',['G8'],'Missing archival header dependency in isolated full-policy reproduction is diagnosed and separately supplemented exporter output equals original reference',[
 'work/full_policy_dependency_supplement_v2_20261021/diagnosis.json','work/full_policy_dependency_supplement_v2_20261021/validation_review.json','work/full_policy_dependency_supplement_v2_20261021/scoped_source_dependency_scan.json'],
 'Original failed attempt retained. Supplement covers weights exporter only, not complete portable artifact/full policy. Scoped1854Pythonfile static scan does not cover arbitrary dynamic dependencies. Corrected five-attempt cohort is separate and awaits original terminal state, not replacement sampling.'),
 ('H8',['G6'],'Isolated power2 delta quotient successor passes75fixture RTL calls and326304actual helper vectors; actual packaged XO source/interface checked',[
 'work/power2_delta_quotient_candidate_20261021/RTL_cosim_review.json','work/power2_delta_quotient_candidate_20261021/HLS_structure_review.json','work/power2_delta_quotient_helper_RTL_20261021/review.json','work/power2_delta_quotient_hw_20261021/XO_interface_review.json'],
 'Check referenced reports for precise finite scope. Full nonzero power2 capacity precondition preserved; helper vectors cover observable low32quotient. No integrated physical link or requested-clock closure for this successor. HLS resource/period estimates are not routed or board performance.'),
 ('H9',['G7'],'Refreshed PCI and XRT observation contains no enumerated physical U280',[
 'work/hardware_availability_refresh_20261021/review.json'],
 'Point-in-time environment observation, not permanent machine claim. No board execution,energy or measured end-to-end acceleration. Compilation/emulation availability does not satisfy physical gate.')]
 ids={c['id'] for c in m['claims']}
 for ident,gates,claim,ev,limits in specs:
  assert ident not in ids
  for name in ev:assert (R/name).is_file(),name
  m['claims'].append(dict(id=ident,gates=gates,claim=claim,status='supported_in_declared_scope',evidence=ev,limits=limits))
  for name in ev:m['source_sha256'][name]=sha(R/name)
 gates=[{k:g[k] for k in ['id','requirement','status']} for g in d['gates']];assert len(gates)==8 and all(g['status']!='complete' for g in gates)
 m.update(schema='dieroute.claim_matrix.v23',recorded_ns=time.time_ns(),gates=gates,predecessor=dict(path=str(old.relative_to(R)),sha256=sha(old)),scope='Original8gates remain open. Additive diagnostic,isolated algorithm and packaging evidence; no revised cohort success or physical result. All original failures and denominators retained.',research_complete=False,board_result=False)
 for p in [old,Path(__file__),out/'plan_snapshot.json']:m['source_sha256'][str(p.relative_to(R))]=sha(p)
 p=out/'matrix.json';p.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n');d['current_claim_matrix']=dict(path=str(p.relative_to(R)),sha256=sha(p),status=m['status'],research_complete=False)
 assert plan.read_bytes()==raw;t=plan.with_name('.research_plan_matrix23.tmp');t.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');os.replace(t,plan)
 review=dict(status='direct_sources_reconciled_original8gates_open',claims=len(m['claims']),direct_sources=len(m['source_sha256']),predecessor_source_drift=drift,open_gates=8,matrix_sha256=sha(p),research_complete=False);(out/'review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps(review))
if __name__=='__main__':main()
