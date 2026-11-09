"""Close disjoint wall-clock phase intervals without attributing residual time."""
import json,sys,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
seq=R/'experiments/native_resume_postroute_cost_profile_adder_2026-10-07';rows=[];bindings={str(Path(__file__)):sha(__file__)}
for i in (1,2,3):
 base=R/f'experiments/native_resume_postroute_cost_profile_adder_step{i}_workflow_2026-10-07';path=base/'first/live.search/receipt.json';r=json.loads(path.read_text());step=json.loads((base/'receipt.json').read_text());bindings[str(path)]=sha(path);bindings[str(base/'receipt.json')]=sha(base/'receipt.json')
 names=[p['phase'] for p in r['phase_timings']];assert len(names)==len(set(names))==10
 assert all(math.isfinite(p['seconds']) and p['seconds']>=0 for p in r['phase_timings']);total=sum(p['seconds'] for p in r['phase_timings']);assert total<=r['producer_seconds']
 children={}
 for kind,phase in [('exchange','local_exchange'),('budget','conditioned_budget_batch')]:
  p=path.parent/kind/'receipt.json';c=json.loads(p.read_text());bindings[str(p)]=sha(p);outer=next(p['seconds'] for p in r['phase_timings'] if p['phase']==phase);assert 0<=c['compiled_child_seconds']<=c['total_seconds']<=outer
  children[kind]=dict(callback_seconds=outer,internal_total_seconds=c['total_seconds'],compiled_child_seconds=c['compiled_child_seconds'],internal_nonchild_seconds=c['total_seconds']-c['compiled_child_seconds'],receipt_and_return_residual_seconds=outer-c['total_seconds'])
 native=next(s['seconds'] for s in step['stages'] if s['stage']=='first');assert native>r['producer_seconds']
 rows.append(dict(index=i,phases=r['phase_timings'],producer_seconds=r['producer_seconds'],unpartitioned_producer_tail_seconds=r['producer_seconds']-total,children=children,native_stage_seconds=native,native_stage_outside_producer_seconds=native-r['producer_seconds']))
assert all(sha(p)==h for p,h in bindings.items())
(seq/'cost_profile.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Disjoint producer wall intervals, nested child clocks explicitly separated. Native stage residual includes startup/copies/exports/request client/native guards/routing/sync/STA/receipt hashing and waiting; no exclusive causal attribution. Timing instrumentation only, not accelerator or performance significance evidence. All components paid in full sequence.'),indent=2)+'\n')
print('PASS',len(rows))
