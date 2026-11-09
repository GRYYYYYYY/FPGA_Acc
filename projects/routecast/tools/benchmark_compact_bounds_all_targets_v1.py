"""Input-only full-target cold/warm cache cost, separate from predictor quality."""
import sys,json,time,hashlib,resource,gc,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from class_cached_rc_endpoint_context_v1 import load_endpoints
from compact_target_raw_bounds_v1 import CompactReverseBounds
D=R/'experiments/compact_bounds_all_targets_cost_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def memory():
 fields={}
 for line in Path('/proc/self/status').read_text().splitlines():
  if line.startswith(('VmRSS:','VmHWM:')):
   k,v,*_=line.split();fields[k[:-1]+'_KiB']=int(v)
 fields['ru_maxrss_KiB']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;return fields
def main():
 D.mkdir(exist_ok=False);protocol=R/'experiments/prospective_external_family_sequential_group_refinement_v1_2026-10-20/protocol.json';c=json.loads(protocol.read_text())['cases'][0];endpoint=Path(c['endpoint']);baseline=R/'experiments/prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'/c['case']/'native_retained/warm_timing_round_updated/round1.json'
 bindings={str(p):sha(p) for p in [Path(__file__),protocol,endpoint,baseline,R/'tools/compact_target_raw_bounds_v1.py',R/'tools/class_cached_rc_endpoint_context_v1.py']};ep=json.loads(endpoint.read_text());bindings.update({v['path']:v['sha256'] for v in ep['inputs'].values()})
 budgets={}
 for q in json.loads(baseline.read_text())['records']:budgets.setdefault(q['sink'],set()).add(q['budget_integer'])
 plan=dict(status='FROZEN_BEFORE_COMPUTE',case=c['case'],targets=len(budgets),target_budget_pairs=sum(map(len,budgets.values())),order='ascending target then ascending budget; cold one maximum budget per target, warm all pairs',payload_limit_bytes=2*2**30,bindings=bindings,scope='Single case all prospective inputs; no target-native labels. Process RSS differences include allocator retention, not exact owned memory. No model quality or whole-pipeline speed claim.')
 (D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');start=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(str(endpoint));load_seconds=time.perf_counter()-start;del nodes;gc.collect();before=memory();cache=CompactReverseBounds(f['row_offsets'],f['dest_ranks'],rc.increments,target_budget_ceilings={t:max(bs) for t,bs in budgets.items()});after_prepare=memory();start=time.perf_counter()
 with (D/'cold_events.jsonl').open('x') as log:
  for i,t in enumerate(sorted(budgets),1):
   a=time.perf_counter();view=cache.bound(t,max(budgets[t]));assert view.get(t)==0;del view;log.write(json.dumps(dict(index=i,target=t,seconds=time.perf_counter()-a,cached_payload_bytes=cache.cached_bytes))+'\n');log.flush()
   if i%128==0:print('COLD',i,len(budgets),cache.cached_bytes,flush=True)
 cold_seconds=time.perf_counter()-start;after_cold=memory();cold_stats=cache.stats();start=time.perf_counter();pairs=0
 for t in sorted(budgets):
  for budget in sorted(budgets[t]):
   view=cache.bound(t,budget);assert view.get(t)==0;del view;pairs+=1
 warm_seconds=time.perf_counter()-start;final_stats=cache.stats();assert final_stats['misses']==len(budgets) and final_stats['evictions']==0 and final_stats['growth_rebuilds']==0;assert final_stats['hits']==pairs
 assert all(sha(p)==h for p,h in bindings.items());result=dict(status='ALL_INPUT_TARGETS_COLD_AND_ALL_BUDGET_VIEWS_WARM_COMPLETE',endpoint_load_seconds=load_seconds,cold_seconds=cold_seconds,warm_seconds=warm_seconds,memory_before_cache=before,memory_after_prepare=after_prepare,memory_after_cold=after_cold,memory_after_warm=memory(),cold_stats=cold_stats,final_stats=final_stats,bindings=bindings,protocol=plan)
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',cold_seconds,warm_seconds,flush=True)
if __name__=='__main__':main()
