"""Registered deterministic-work/native-QoR screen; never infer full-time gain."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
S=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18';D=R/'experiments/mmc_v2_native_utility_v1_2026-10-18';pp=S/'protocol.json';P=json.loads(pp.read_text());cp=D/'cohort_complete.json';C=json.loads(cp.read_text());assert C['all15_native_FULL_physical_and_canonical_semantic_pass'];bindings={**C['bindings'],**closure([Path(__file__)]),str(cp):sha(cp),str(pp):sha(pp)};cases=[]
ip=D/'independent_wire_work_verification_v1.json';iv=json.loads(ip.read_text());assert iv['all15_original_XML_wire_and_log_work_counters_independently_equal'];bindings.update(iv['bindings']);bindings[str(ip)]=sha(ip)
for case in P['case_order']:
 proof=D/case/'verification.json';v=json.loads(proof.read_text());assert v['all_native_physical_and_canonical_pass'] and len(v['rows'])==5 and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(proof)]=sha(proof);arms={x['arm']:x for x in v['rows']};assert set(arms)==set(P['native_arm_order']);summary={}
 for name,r in arms.items():
  assert r['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and r['exit_status']==0 and r['canonical']['semantic_consistency_gate_pass'];summary[name]=dict(iterations=r['iterations'],heap_pushes=r['native_work']['total_heap_pushes'],rerouted_NET_operations=r['native_work']['total_rerouted_NET_operations'],rerouted_connection_operations=r['native_work']['total_rerouted_connection_operations'],wirelength=r['wirelength'],diagnostic_cpd_ns=r['diagnostic_cpd_ns'],canonical_fixups=r['canonical']['fixups'],original_zero_counter_gate_pass=r['canonical']['original_zero_counter_gate_pass'],native_component_seconds=r['native_process_seconds'])
 checks=[];candidate=summary[P['primary_candidate']]
 for control in P['controls']:
  baseline=summary[control];checks.append(dict(control=control,heap_pushes_strictly_lower=candidate['heap_pushes']<baseline['heap_pushes'],wirelength_nonworse=candidate['wirelength']<=baseline['wirelength'],diagnostic_CPD_nonworse=candidate['diagnostic_cpd_ns']<=baseline['diagnostic_cpd_ns']))
 frontier=[name for name,a in summary.items() if not any(all(b[k]<=a[k] for k in ['heap_pushes','wirelength','diagnostic_cpd_ns']) and any(b[k]<a[k] for k in ['heap_pushes','wirelength','diagnostic_cpd_ns']) for other,b in summary.items() if other!=name)]
 passed=all(x['heap_pushes_strictly_lower'] and x['wirelength_nonworse'] and x['diagnostic_CPD_nonworse'] for x in checks);cases.append(dict(case=case,arms=summary,descriptive_native_heap_wire_diagnosticCPD_frontier=frontier,primary_screen_checks=checks,pass_registered_utility_screen=passed));print('V2UTILITY SCREEN',case,passed,checks,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'utility_screen_v1.json').open('x') as f:json.dump(dict(status='closed_verified',bindings=bindings,cases=cases,primary_candidate=P['primary_candidate'],all3_registered_utility_screens_pass=all(c['pass_registered_utility_screen'] for c in cases),scope='Deterministic native work/wire/diagnostic CPD correctness pilot on exposed layouts. Frontier is descriptive over those3native metrics only, not full-flow cost or a replacement for the registered screen. All forecast-quality failures remain. Cases were concurrent and arm order unbalanced; cached seed/prefix/export and canonical costs excluded from native clocks. No end-to-end speedup, heldout, source minima or hardware claim.'),f,indent=2)
