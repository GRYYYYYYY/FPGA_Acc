"""Explain iteration-counter shape after independent six-run admission, no new solver runs."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
D=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18';proof=D/'independent_wire_work_comparison_v1.json';v=json.loads(proof.read_text());assert v['status']=='pass' and v['all6_independent_wire_and_every_iteration_integer_fields_equal'];bindings={**v['bindings'],str(proof):sha(proof),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};assert all(sha(p)==h for p,h in bindings.items());results=[]
for case in ['case_01','case_02','case_03']:
 vp=D/case/'verification.json';cv=json.loads(vp.read_text());assert cv['all_native_physical_and_canonical_pass'];bindings[str(vp)]=sha(vp);rows={r['arm']:r['native_work']['rows'] for r in cv['rows']};summaries={}
 for arm,rs in rows.items():
  # Every integer in these rows was checked lexically in the bound independent comparison.
  peak=max(rs,key=lambda x:x['overused_RR_nodes']);heaps=sum(x['heap_pushes'] for x in rs)
  summaries[arm]=dict(iterations=len(rs),first_iteration=rs[0],peak_overuse=dict(iteration=peak['iteration'],overused_RR_nodes=peak['overused_RR_nodes']),total_heap_pushes=heaps,post_first_heap_pushes=heaps-rs[0]['heap_pushes'],iterations_with_exactly_one_overused_RR_node=[x['iteration'] for x in rs if x['overused_RR_nodes']==1])
 off=rows['off'];on=rows['on'];extra=on[len(off):];results.append(dict(case=case,observations=summaries,on_iterations_after_off_completion=len(extra),on_heap_pushes_after_off_iteration_count=sum(x['heap_pushes'] for x in extra),on_heap_share_after_off_iteration_count=sum(x['heap_pushes'] for x in extra)/summaries['on']['total_heap_pushes']))
assert all(sha(p)==h for p,h in bindings.items())
with (D/'convergence_shape_diagnostic_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=results,scope='Retrospective shape of independently verified native iteration counters. One overused RR node is not one overflow unit or an identified owner. No claim about net identities, full timing, causal congestion propagation or a tuned acceptance policy.'),f,indent=2)
print(json.dumps(results),flush=True)
