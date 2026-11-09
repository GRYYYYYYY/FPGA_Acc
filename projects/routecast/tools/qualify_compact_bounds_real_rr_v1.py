"""Deterministic first-eight-target RR contract microbenchmark; not model timing."""
import sys,json,time,hashlib,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from class_cached_rc_endpoint_context_v1 import load_endpoints
from compact_target_raw_bounds_v1 import CompactReverseBounds
from reverse_raw_delay_bounds_v1 import ReverseBounds
D=R/'experiments/compact_bounds_real_rr_microbenchmark_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);protocol=R/'experiments/prospective_external_family_sequential_group_refinement_v1_2026-10-20/protocol.json';c=json.loads(protocol.read_text())['cases'][0];endpoint=Path(c['endpoint']);start=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(str(endpoint));load_seconds=time.perf_counter()-start
 baseline=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'/c['case']/'native_retained/warm_timing_round_updated/round1.json';ep=json.loads(baseline.read_text());budgets={}
 for q in ep['records']:
  target=q['sink'];budget=q['budget_integer'];budgets.setdefault(target,set()).add(budget)
 targets=sorted(budgets)[:8];ceilings={t:max(budgets[t]) for t in targets};cache=CompactReverseBounds(f['row_offsets'],f['dest_ranks'],rc.increments,target_budget_ceilings=ceilings);reference=ReverseBounds(f['row_offsets'],f['dest_ranks'],rc.increments);rows=[]
 for target in targets:
  for budget in sorted(budgets[target]):
   a=time.perf_counter();actual=cache.bound(target,budget);compact_seconds=time.perf_counter()-a;a=time.perf_counter();expected=reference.bound(target,budget);legacy_seconds=time.perf_counter()-a
   assert actual.context==expected.context
   assert all(actual.get(n)==expected.get(n) for n in range(cache.n))
   a=time.perf_counter();again=cache.bound(target,budget);assert all(again.get(n)==expected.get(n) for n in range(cache.n));warm_access_and_full_compare_seconds=time.perf_counter()-a
   rows.append(dict(target=target,budget=budget,compact_bound_seconds=compact_seconds,legacy_bound_seconds=legacy_seconds,warm_access_and_full_compare_seconds=warm_access_and_full_compare_seconds));print('VERIFIED',target,budget,flush=True)
 result=dict(status='REAL_RR_FIRST_EIGHT_INPUT_TARGETS_ALL_NODE_LEGACY_PARITY_PASS',nodes=cache.n,arcs=cache.m,endpoint_load_seconds=load_seconds,rows=rows,compact_stats=cache.stats(),legacy_preparation_seconds=reference.preparation_seconds,legacy_bound_seconds=reference.bound_seconds,process_peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,bindings={str(p):sha(p) for p in [Path(__file__),endpoint,protocol,baseline,R/'tools/compact_target_raw_bounds_v1.py',R/'tools/reverse_raw_delay_bounds_v1.py']},scope='Deterministic input-only first eight sorted targets, all their input budgets. Full-node equality against legacy. Combined process RSS includes XML, both caches and verification; not isolated cache RSS, whole-cohort or predictor speed evidence.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
