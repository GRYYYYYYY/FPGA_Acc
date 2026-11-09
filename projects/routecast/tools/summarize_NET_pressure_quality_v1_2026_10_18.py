"""Paired all-source NET diagnostic interpretation without policy promotion."""
import hashlib,itertools,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/mmc_NET_pressure_quality_verification_v1_2026-10-18');vp=out/'verification.json';v=json.loads(vp.read_text());assert v['status']=='pass' and v['cells_verified']==540
 for p,h in v['bindings'].items():assert sha(p)==h
 root=Path('experiments/mmc_NET_pressure_quality_v1_2026-10-18');rp=root/'results.json';r=json.loads(rp.read_text());planpath=Path('experiments/mmc_NET_pressure_exposure_v1_2026-10-18/protocol.json');plan=json.loads(planpath.read_text());rows=r['rows'];index={(x['case'],x['policy'],x['target'],x['source'],x['method']):x for x in rows}
 controls=[m for m in plan['methods'] if m!=plan['primary_score']];comparisons={}
 def trend(pairs,get):
  counts={k:0 for k in ['up','down','equal','undefined']}
  for a,b in pairs:
   x,y=get(a),get(b)
   if x is None or y is None:counts['undefined']+=1
   elif x>y+1e-12:counts['up']+=1
   elif x<y-1e-12:counts['down']+=1
   else:counts['equal']+=1
  return counts
 getters={'spearman':lambda r:r['metrics']['spearman'],'deterministic_P_at_K':lambda r:r['metrics']['precision_at_k'],'target_count_capture_fraction':lambda r:r['target_count_capture_fraction']}
 for control in controls:
  comparisons[control]={}
  for target in plan['targets']:
   pairs=[(index[c,p,target,s,plan['primary_score']],index[c,p,target,s,control]) for c,p,s in itertools.product(plan['cases'],plan['policies'],plan['sources'])]
   comparisons[control][target]={name:trend(pairs,get) for name,get in getters.items()}
 primary=[]
 for case,policy,target in itertools.product(plan['cases'],plan['policies'],plan['targets']):
  selected={m:index[case,policy,target,plan['primary_source'],m] for m in plan['methods']}
  primary.append(dict(case=case,policy=policy,target=target,total_target_count=selected[plan['primary_score']]['total_target_count'],methods={m:dict(spearman=x['metrics']['spearman'],deterministic_P_at_K=x['metrics']['precision_at_k'],captured_target_count=x['selected_target_count'],capture_fraction=x['target_count_capture_fraction'],enrichment=x['enrichment_over_uniform_selection']) for m,x in selected.items()}))
 receipt=dict(status='all540_NET_exposure_cells_verified_no_native_policy_promotion',bindings={str(p.resolve()):sha(p) for p in [vp,rp,planpath,Path(__file__)]},cells=540,NETs=55300,topK=2765,fixed_primary_source=plan['primary_source'],fixed_primary_score=plan['primary_score'],primary_target=plan['primary_target'],all_source_comparisons=comparisons,fixed_primary_source_results=primary,findings=['For the fixed retained_on source, anchored sums improve total route-operation Spearman and captured count over length-only and raw density in all6case/policy pairs, but lose both metrics to uniform risk in all6pairs. RR-level anchored gains do not transfer to NET aggregation automatically.','First-iteration overuse flags are sparse under on-policy traces; current observed-overflow sums capture more of these observed flags than the uncertain priors. A zero flag may mean another native guard was first, not no need to route.','Total-overuse and total-operation targets are highly related: most admitted true guards are overuse. They are not independent replications.'],limits=['These are exposed observational events from fixed seed policies, not effects of changing NET order, seed retention or route choices.','Successful wholeNET operations are not per-NET heap work, connection reroute count, elapsed time or sole causal repair necessity.','Uniform risk remains an existing control; do not retroactively replace the frozen anchored primary or select per-case winners.','All original cold/native utility/unseen and complete-time/hardware requirements remain unmet.'],next_action='Do not tune mixture weights or start a native policy run solely from these observational ranks. Inspect the existing strict-unseen/family admission requirements and source inventory, then establish a prospective independently sourced family/cohort before testing any new pressure-guided decision. Freeze matched graph/placement, source-cost accounting, length/raw/uniform controls, target semantics and native QoR gates before labels. Keep the unresolved source-only inter-group redistribution problem explicit.')
 with (out/'research_decision_v1.json').open('x') as f:json.dump(receipt,f,indent=2)
 print(json.dumps(dict(primary_total_operation_comparisons=[x for x in primary if x['target']==plan['primary_target']],all_source_total_operation_capture={c:comparisons[c][plan['primary_target']]['target_count_capture_fraction'] for c in controls})))
if __name__=='__main__':main()
