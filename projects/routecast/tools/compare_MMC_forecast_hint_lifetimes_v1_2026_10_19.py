"""Posthoc lifetime comparison with zero-control bridge and actual first-prefix identity."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def first_prefix(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for line in f:
   h.update(line)
   if line==b'CP iteration_begin 2\n':return h.hexdigest()
 return None
def main():
 oldp=R/'experiments/mmc_native_excess_utility_review_v1_2026-10-19/comparison.json';newp=R/'experiments/mmc_first_iteration_hint_utility_review_v1_2026-10-19/comparison.json'
 if not newp.exists():raise SystemExit('NOT_READY: all6 replay and component comparison required; no output created')
 old=json.loads(oldp.read_text());new=json.loads(newp.read_text());bindings={str(p):sha(p) for p in [oldp,newp,pathlib.Path(__file__).resolve()]};rows=[]
 for case in ['episode_01','episode_02','episode_03']:
  a=next(x for x in old['cases'] if x['case']==case);b=next(x for x in new['cases'] if x['case']==case);assert a['arms']['zero']['work']==b['arms']['zero']['work'] and a['arms']['zero']['wirelength']==b['arms']['zero']['wirelength'] and a['arms']['zero']['diagnostic_cpd_ns']==b['arms']['zero']['diagnostic_cpd_ns'];A=R/'experiments/mmc_native_excess_utility_v1_2026-10-19'/case;B=R/'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19'/case
  for name in ['design.blif','design.net','design.place']:
   assert (A/'forecast/cold'/name).read_bytes()==(B/'forecast/cold'/name).read_bytes()
  x=A/'forecast/cold/preload_state.bin';y=B/'forecast/cold/preload_state.bin';initial_same=x.read_bytes()==y.read_bytes();assert initial_same;tx=A/'forecast/cold/owner_trace.tsv';ty=B/'forecast/cold/owner_trace.tsv';prefix_a,prefix_b=first_prefix(tx),first_prefix(ty);prefix_same=prefix_a is not None and prefix_a==prefix_b
  oldzero=A/'zero/cold/owner_trace.tsv';newzero=B/'zero/cold/owner_trace.tsv';assert sha(oldzero)==sha(newzero)
  persistent=a['arms']['forecast'];first=b['arms']['forecast'];rows.append(dict(case=case,initial_cost_bits_exactly_same=initial_same,first_iteration_owner_trace_prefix_same=prefix_same,complete_zero_control_owner_trace_same=True,first_minus_persistent_work={k:first['work'][k]-persistent['work'][k] for k in first['work']},first_minus_persistent_iterations=first['iterations']-persistent['iterations'],first_minus_persistent_wirelength=first['wirelength']-persistent['wirelength'],original_primary_gate_persistent=a['primary_native_component_gate_pass'],original_primary_gate_first_iteration=b['primary_native_component_gate_pass']))
  for p in [x,y,tx,ty,oldzero,newzero]:bindings[str(p)]=sha(p)
  print('HINT_LIFETIME_COMPARISON',rows[-1],flush=True)
 O=R/'experiments/mmc_forecast_hint_lifetime_comparison_v1_2026-10-19';O.mkdir(exist_ok=False);(O/'review.json').open('x').write(json.dumps(dict(status='ALL3_INITIAL_COST_ZERO_BRIDGE_AND_FIRST_PREFIX_LIFETIME_COMPARISON_COMPLETE',cases=rows,bindings=bindings,scope='Posthoc work-count comparison of fixed permanent vs first-iteration-only hint studies on exposed development cases. Distinct binaries with same source base; actual zero trajectories and first prefixes checked, no universal binary equivalence or sole-cause claim. Original zero-relative utility gates unchanged; no new sweep, metric selection, full-flow timing or hardware gain.'),indent=2)+'\n')
if __name__=='__main__':main()
