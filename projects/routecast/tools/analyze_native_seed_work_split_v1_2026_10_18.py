"""Exact observed seed/other heap-push decomposition under archived native policies."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 root=R/'experiments/mmc_native_seed_context_replay_v1_2026-10-18';rp=root/'verification.json';vp=root/'independent_verification_v1.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert len(r['rows'])==len(v['rows'])==6 and v['status']=='all693432CID_seed_count_unique_sum_and_attempt_vectors_independently_verified';assert sha(rp)==v['bindings'][str(rp)];pairs=[]
 for case in ['case_01','case_02','case_03']:
  arms={}
  for arm in ['off','on']:
   row=next(x for x in r['rows'] if x['case']==case and x['arm']==arm);check=next(x for x in v['rows'] if x['case']==case and x['arm']==arm);assert check['inside_seed_pushes']==row['inside_seed_pushes'] and check['outside_seed_pushes']==row['outside_seed_pushes']==0;seed=row['inside_seed_pushes'];total=row['all_sink_heap_pushes'];other=total-seed;assert other>=0;arms[arm]=dict(attempts=row['attempts'],seed_heap_pushes=seed,other_heap_pushes=other,total_heap_pushes=total,total_heap_pops=row['all_sink_heap_pops'],seed_share=seed/total,mean_seed_pushes_per_attempt=seed/row['attempts'],max_seed_pushes_per_attempt=row['max_seed_pushes_per_attempt'])
  delta={k:arms['on'][k]-arms['off'][k] for k in ['attempts','seed_heap_pushes','other_heap_pushes','total_heap_pushes','total_heap_pops']};assert delta['total_heap_pushes']==delta['seed_heap_pushes']+delta['other_heap_pushes'];pairs.append(dict(case=case,arms=arms,on_minus_off=delta))
 bindings={str(p):sha(p) for p in [rp,vp,Path(__file__)]};result=dict(status='all3_exact_native_seed_other_heap_work_decompositions_pass',bindings=bindings,pairs=pairs,scope='Off/on is native first-iteration partial-tree preservation, not RouteCast algorithm toggle. Seed heap pushes may include internal fallback and repeated entries; other means remaining measured heap pushes, not independently timed expansion cost. Counts decompose arithmetically, do not establish walltime causality, acceptable route quality or full-flow gain. All3exposed observations retained; original cold/native/failure/heldout/hardware requirements unchanged.')
 with (root/'seed_work_split_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(pairs,indent=2),flush=True)
if __name__=='__main__':main()
