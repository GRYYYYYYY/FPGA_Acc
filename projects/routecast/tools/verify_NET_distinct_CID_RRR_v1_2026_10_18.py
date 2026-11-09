"""Reverse CID grouping, independent ranks/heap selection and exact Schur moments."""
import sys,json,array,math,heapq,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from diagnose_NET_length_confounding_v1_2026_10_18 import rank

def main():
 E=R/'experiments';d=E/'mmc_NET_distinct_CID_RRR_v1_2026-10-18';rp=d/'results.json';r=json.loads(rp.read_text());tm=json.loads((d/'target_manifest.json').read_text());sm=json.loads((E/'mmc_NET_pressure_exposure_v1_2026-10-18/vector_manifest.json').read_text());dom=json.loads((E/'mmc_NET_pressure_exposure_v1_2026-10-18/NET_domains.json').read_text());labels=json.loads((E/'mmc_native_connection_CID_binding_v1_2026-10-18/verification.json').read_text());cache={};checked=0;max_partial_error=0
 def read(desc,kind):
  p=desc['path']
  if p not in cache:
   assert sha(p)==desc['sha256'];a=array.array(kind);a.frombytes(Path(p).read_bytes());assert len(a)==desc['values'];cache[p]=a
  return cache[p]
 def ranks(v):
  n=len(v);return [int(2*x-(n-1)) for x in rank(v)]
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def rho(a,b):
  q=dot(a,a)*dot(b,b);return dot(a,b)/math.sqrt(q) if q else None
 for case in ['case_01','case_02','case_03']:
  ep=json.loads((E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json').read_text());ids=dom[case]['NET_ids'];members=collections.defaultdict(list)
  for q in ep['connections']:members[q['net_id']].append(q['connection_id'])
  assert ids==sorted(members) and sum(map(len,members.values()))==115572;N=len(ids);K=N//20;fan=read(tm[case+'__fanout'],'Q');assert list(fan)==[len(members[n]) for n in ids];fc=ranks(fan);targets={}
  for policy in ['off','on']:
   desc=next(v for v in labels['rows'] if v['case']==case and v['arm']==policy)['vectors']['observed_explicit_reroute'];bits=read(desc,'B');count=read(tm[case+'__'+policy+'__count'],'Q');fraction=read(tm[case+'__'+policy+'__fraction'],'d')
   for i,n in enumerate(ids):assert count[i]==sum(bits[cid] for cid in members[n]) and fraction[i]==count[i]/len(members[n])
   targets[policy]=(count,fraction)
  for source in sorted({x['source'] for x in r['rows']}):
   length=read(sm[case+'__'+source+'__unique_node_count'],'d');lc=ranks(length);ll,ff,lf=dot(lc,lc),dot(fc,fc),dot(lc,fc);det=ll*ff-lf*lf;assert det>0;xcached={}
   for row in [x for x in r['rows'] if x['case']==case and x['source']==source]:
    method=row['method'];x=fan if method=='manifest_fanout' else read(sm[case+'__'+source+'__'+method],'d');count,fraction=targets[row['policy']];y=count if row['target']=='count' else fraction
    if method not in xcached:xcached[method]=(ranks(x),set(heapq.nsmallest(K,range(N),key=lambda i:(-x[i],ids[i]))))
    xr,selected=xcached[method];yr=ranks(y);actual=rho(xr,yr);expected=row['spearman'];assert (actual is None)==(expected is None)
    if actual is not None:assert abs(actual-expected)<1e-12
    xx,yy,xy=dot(xr,xr),dot(yr,yr),dot(xr,yr);xl,xf,yl,yf=dot(xr,lc),dot(xr,fc),dot(yr,lc),dot(yr,fc);vx=xx*det-xl*xl*ff+2*xl*xf*lf-xf*xf*ll;vy=yy*det-yl*yl*ff+2*yl*yf*lf-yf*yf*ll;cov=xy*det-xl*yl*ff+(xl*yf+xf*yl)*lf-xf*yf*ll;assert vx>=0 and vy>=0;partial=cov/math.sqrt(vx*vy) if vx and vy else None;expected=row['partial_rank_correlation_controlling_length_and_fanout'];assert (partial is None)==(expected is None)
    if partial is not None:error=abs(partial-expected);max_partial_error=max(max_partial_error,error);assert error<1e-9
    truth_top=set(heapq.nsmallest(K,range(N),key=lambda i:(-y[i],ids[i])));assert len(selected&truth_top)/K==row['deterministic_precision_at_K'];boundary=min(y[i] for i in truth_top);strict=sum(y[i]>boundary for i in selected);all_above=sum(v>boundary for v in y);all_equal=sum(v==boundary for v in y);inside=sum(y[i]==boundary for i in selected);slots=K-all_above;interval=[strict+max(0,slots-(all_equal-inside)),strict+min(slots,inside)];assert interval==row['truth_tie_hit_bounds'];capture=sum(count[i] for i in selected)/sum(count);mean=math.fsum(fraction[i] for i in selected)/K;assert abs(capture-row['distinct_rerouted_CID_capture'])<1e-12 and abs(mean-row['selected_NET_mean_reroute_fraction'])<1e-12;checked+=1
  print('CID NET MATRIX INDEPENDENT CASE PASS',case,flush=True)
 assert checked==432
 for p,h in r['bindings'].items():assert sha(p)==h
 fixed=[x for x in r['rows'] if x['source']=='native_retained_on'];index={(x['case'],x['policy'],x['target'],x['method']):x for x in fixed};pairs=[(c,p) for c in ['case_01','case_02','case_03'] for p in ['off','on']];summary={}
 for method in ['anchored_risk_sum','uniform_risk_sum']:
  count=[index[c,p,'count',method] for c,p in pairs];fanout=[index[c,p,'count','manifest_fanout'] for c,p in pairs];partial=[x['partial_rank_correlation_controlling_length_and_fanout'] for x in count];summary[method]=dict(fanout_has_higher_count_spearman_pairs=sum(b['spearman']>a['spearman'] for a,b in zip(count,fanout)),fanout_has_higher_CID_capture_pairs=sum(b['distinct_rerouted_CID_capture']>a['distinct_rerouted_CID_capture'] for a,b in zip(count,fanout)),partial_count_rank_range=[min(partial),max(partial)])
 result=dict(status='all432_complete_CID_NET_target_rank_capture_and_two_control_statistics_verified',bindings={str(p):sha(p) for p in [rp,d/'target_manifest.json',Path(__file__),R/'tools/diagnose_NET_length_confounding_v1_2026_10_18.py']},cells_verified=checked,max_partial_formula_error=max_partial_error,fixed_primary_source_summary=summary,decision='Risk scores retain conditional association but do not beat manifest fanout in primary-source count correlation/capture for any of6pairs. Add fanout as mandatory cheap baseline for any future CID-work decision; do not start native policy trial or replace old gates from these observational statistics. Same3exposed layouts/policies are not independent families; no per-CID timing or complete-time gain.')
 with (d/'verification_and_decision_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
