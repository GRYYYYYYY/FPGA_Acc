"""Independent off/on first-pass partialNET wire/work comparison, exposed cases only."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from native_wire_work_independent_v2 import read_spans,audit
D=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18';cp=D/'cohort_complete.json';C=json.loads(cp.read_text());assert C['all6_off_on_complete_FULL_physical_canonical_pass'] and C['all3_flag_off_equal_supported_engine_partial_controls'];bindings={**C['bindings'],**closure([Path(__file__)]),str(cp):sha(cp)};cache=Cache();rows=[]
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(g['previous_endpoint']).read_text());spans=read_spans(ep['inputs']['graph']['path'],ep['graph_sha256'])
 for case in ['case_01','case_02','case_03']:
  vp=D/case/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'];bindings[str(vp)]=sha(vp);summaries={}
  for r in v['rows']:
   W=D/case/r['arm'];physical=json.loads((W/'physical_audit.json').read_text());a=audit(W/'native.log',W/'output.route',physical,spans)
   assert a['wirelength']==r['wirelength'] and a['iterations']==r['iterations'] and len(a['rows'])==len(r['native_work']['rows'])
   for actual,expected in zip(a['rows'],r['native_work']['rows']):assert all(actual[k]==expected[k] for k in actual)
   for k in ['heap_pushes','rerouted_NET_operations','rerouted_connection_operations']:assert a[k]==r['native_work']['total_'+k]
   summaries[r['arm']]={k:x for k,x in a.items() if k!='rows'};summaries[r['arm']].update(first_iteration=a['rows'][0],diagnostic_cpd_ns=r['diagnostic_cpd_ns'],canonical_fixups=r['canonical']['fixups'],original_zero_counter_gate_pass=r['canonical']['original_zero_counter_gate_pass'])
  off=summaries['off'];on=summaries['on'];row=dict(case=case,observations=summaries,on_minus_off={k:on[k]-off[k] for k in ['iterations','wirelength','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','diagnostic_cpd_ns']},heap_reduction=1-on['heap_pushes']/off['heap_pushes']);rows.append(row);print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_wire_work_comparison_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all6_independent_wire_and_every_iteration_integer_fields_equal=True,scope='Controlled exposed-case mechanism ablation; diagnostic CPD only. No fresh full-flow timing gain, forecast-quality success, unseen-family or hardware claim. Original failed utility screen unchanged.'),f,indent=2)
