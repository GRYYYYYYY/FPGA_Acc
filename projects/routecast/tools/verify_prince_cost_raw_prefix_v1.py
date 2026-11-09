"""Exact saved QueryKey byte/order equality, beyond noncryptographic summaries."""
import json,filecmp
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_cost_raw_prefix_trial_v1_2026-10-20';S=E/'prince_cost_advance_ablation_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def same(a,b):return filecmp.cmp(a,b,shallow=False)
def main():
 vp=D/'verification.json';v=load(vp);full=load(S/'verification.json');by={r['case']:r for r in v['rows']};assert len(by)==36 and all(r['full_study_prefix_counts_FNV_RR_BB_owners_equal'] for r in v['rows']);comparisons=prefix=post=0;rows=[];intentional=0
 for base in sorted({r['case'].rsplit('/',1)[0] for r in v['rows']}):
  control=by[base+'/native'];ready=control['ready_iteration'];limit=ready if ready else control['observed_phases'];control_dir=D/base/'native/raw_queries'
  for mode in ['native','hold_pres','hold_acc','hold_both']:
   r=by[base+'/'+mode];assert r['ready_iteration']==ready;intentional+=r['status']=='INTENTIONAL_PREFIX_VALIDATION_NOT_ROUTING_SUCCESS';assert r['observed_phases']==(ready+1 if ready else control['observed_phases'])
   if mode=='native':continue
   for i in range(1,limit+1):
    assert same(control_dir/f'phase_{i}.bin',D/base/mode/'raw_queries'/f'phase_{i}.bin'),(base,mode,i,'prefix bytes/order');comparisons+=1;prefix+=1
  if ready:
   i=ready+1
   for left,right in [('native','hold_acc'),('hold_pres','hold_both')]:
    assert same(D/base/left/'raw_queries'/f'phase_{i}.bin',D/base/right/'raw_queries'/f'phase_{i}.bin'),(base,left,right,'first post bytes/order');comparisons+=1;post+=1
   rows.append(dict(case=base,first_post_native_hold_acc_bytes_equal=True,first_post_hold_pres_hold_both_bytes_equal=True,first_post_hold_pres_differs_from_native=not same(D/base/'native/raw_queries'/f'phase_{i}.bin',D/base/'hold_pres/raw_queries'/f'phase_{i}.bin')))
  print('RAW_QUERY_EXACT_BYTE_ORDER_PASS',base,limit,flush=True)
 assert prefix==447 and post==12 and comparisons==459 and intentional==24;assert len(full['rows'])==36
 out=dict(status='ALL36_REPRODUCED_PREFIXES_EXACT_OBSERVED_QUERY_BYTES_AND_ORDER_PASS',prefix_byte_comparisons=prefix,first_post_byte_comparisons=post,total_deep_byte_comparisons=comparisons,intentional_validation_stops=24,full_unactivated_failures=12,raw_query_calls=sum(r['observed_query_calls'] for r in v['rows']),raw_query_bytes=sum(r['raw_query_bytes'] for r in v['rows']),first_post_response=rows,bindings={str(p):sha(p) for p in [vp,D/'protocol.json',S/'verification.json',Path(__file__)]},scope='Direct full byte comparison of separate per-phase saved native QueryKey streams;collector counts and native SHA256 independently checked by reproduction runner. Reproduced counters/FNV/RR/BB/owners agree original full-study prefixes. Observed linker paths only,no every-inlined-cost-path claim. Intentional stops never count as legal full routing or predictor labels.')
 with (D/'exact_byte_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print('EXACT_RAW_QUERY_VALIDATION_COMPLETE',comparisons,out['raw_query_bytes'])
if __name__=='__main__':main()
