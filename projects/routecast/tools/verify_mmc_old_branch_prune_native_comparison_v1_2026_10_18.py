"""Independent supplemental partialNET native wire/work and reference comparison."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from native_wire_work_independent_v1 import read_spans,audit
D=R/'experiments/mmc_old_branch_prune_native_v1_2026-10-18';cp=D/'cohort_complete.json';C=json.loads(cp.read_text());assert C['all3_partialNET_controls_complete_FULL_physical_canonical_pass'] and C['all3_new_engine_cold_references_equal_original'];bindings={**C['bindings'],**closure([Path(__file__)]),str(cp):sha(cp)};core=R/'experiments/native_wire_work_independent_core_v1_2026-10-18/verification.json';cv=json.loads(core.read_text());assert cv['status']=='pass';bindings.update(cv['bindings']);bindings[str(core)]=sha(core);cache=Cache();rows=[]
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items());g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(g['previous_endpoint']).read_text());spans=read_spans(ep['inputs']['graph']['path'],ep['graph_sha256'])
 for case in ['case_01','case_02','case_03']:
  vp=D/case/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp);summaries={}
  for r in v['rows']:
   W=D/case/r['arm'];p=json.loads((W/'physical_audit.json').read_text());a=audit(W/'native.log',W/'output.route',p,spans);assert a['wirelength']==r['wirelength'] and a['iterations']==r['iterations'];assert len(a['rows'])==len(r['native_work']['rows'])
   for actual,expected in zip(a['rows'],r['native_work']['rows']):assert all(actual[k]==expected[k] for k in actual)
   for k in ['heap_pushes','rerouted_NET_operations','rerouted_connection_operations']:assert a[k]==r['native_work']['total_'+k]
   summaries[r['arm']]={k:x for k,x in a.items() if k!='rows'};summaries[r['arm']].update(diagnostic_cpd_ns=r['diagnostic_cpd_ns'],canonical_fixups=r['canonical']['fixups'],original_zero_counter_gate_pass=r['canonical']['original_zero_counter_gate_pass'])
  if case=='case_01':
   Q=R/'experiments/mmc_partial_seed_engine_equivalence_v1_2026-10-18';qv=json.loads((Q/'verification.json').read_text());r=next(x for x in qv['rows'] if x['arm']=='cold');p=json.loads((Q/'cold/physical_audit.json').read_text());a=audit(Q/'cold/native.log',Q/'cold/output.route',p,spans);summaries['cold']={k:x for k,x in a.items() if k!='rows'};summaries['cold']['diagnostic_cpd_ns']=r['diagnostic_cpd_ns']
  reference=R/'experiments/mmc_v2_native_utility_v1_2026-10-18'/case/'verification.json';rv=json.loads(reference.read_text());assert rv['all_native_physical_and_canonical_pass'];bindings[str(reference)]=sha(reference);branch=summaries['old_branch_prune'];checks=[]
  for name in ['retained_off','retained_on','raw_off','trim']:
   r=next(x for x in rv['rows'] if x['arm']==name);checks.append(dict(reference=name,branch_heap_pushes_minus_reference=branch['heap_pushes']-r['native_work']['total_heap_pushes'],branch_wire_minus_reference=branch['wirelength']-r['wirelength'],branch_diagnostic_CPD_minus_reference=branch['diagnostic_cpd_ns']-r['diagnostic_cpd_ns']))
  row=dict(case=case,same_build_observations=summaries,original15arm_reference_deltas=checks,same_build_branch_heap_reduction_vs_cold=1-branch['heap_pushes']/summaries['cold']['heap_pushes']);rows.append(row);print('PARTIAL BRANCH CONTROL',row,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_wire_work_comparison_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all_partial_controls_and_same_build_cold_wire_work_replayed=True,scope='Supplemental descriptive control, not replacement for failed15arm screen. New-build cold matches original in all3cases, and completeNET seed equivalence tested oncase01; old15arm seed deltas remain cross-build references. Component clocks concurrent/cached/unbalanced; no full-flow benefit, promotion, unseen or hardware claim.'),f,indent=2)
