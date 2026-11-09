"""Independent histogram ranks, topK and exact integer Schur partial correlations."""
import pathlib,json,hashlib,array,math,heapq
from collections import Counter,defaultdict
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def centered(values):
 counts=Counter(values);offset=0;ranks={};n=len(values)
 for x,count in sorted(counts.items()):ranks[x]=2*offset+count-n;offset+=count
 return [ranks[x] for x in values]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def main():
 O=R/'experiments/mmc_current_NET_exposure_work_diagnostic_v1_2026-10-19';rp=O/'results.json';r=json.loads(rp.read_text());assert r['status']=='ALL27_FIXED_CURRENT_NET_EXPOSURE_DIAGNOSTIC_CELLS_COMPUTED' and len(r['rows'])==27
 for p,h in r['bindings'].items():assert sha(pathlib.Path(p))==h
 M=R/'experiments/mmc_first_hint_connection_work_replay_v1_2026-10-19';measured=json.loads((M/'verification.json').read_text());bindings={str(p):sha(p) for p in [rp,pathlib.Path(__file__).resolve()]};verified=0;max_error=0
 for case in ['episode_01','episode_02','episode_03']:
  ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19'/case/'demand/endpoints.json';members=defaultdict(list)
  for q in json.loads(ep.read_text())['connections']:members[q['net_id']].append(q['connection_id'])
  ids=sorted(members);assert len(ids)==55300;K=2765;fp=R/'experiments/mmc_current_NET_exposure_features_v1_2026-10-19'/(case+'.jsonl');fs={x['net_id']:x for x in map(json.loads,fp.read_text().splitlines())};methods=['manifest_fanout','expected_CHANNEL_span','expected_penalty_exposure'];scores={m:[Fraction(fs[n][m]) for n in ids] for m in methods};rank={m:centered(x) for m,x in scores.items()};targets={}
  for arm,name in [('zero','zero_heap_pushes'),('forecast','first_hint_heap_pushes')]:
   desc=next(x for x in measured['rows'] if x['case']==case and x['arm']==arm)['vectors']['heap_pushes'];p=pathlib.Path(desc['path']);assert desc['sha256']==sha(p);values=array.array('Q');values.frombytes(p.read_bytes());targets[name]=[sum(values[c] for c in members[n]) for n in ids]
  targets['first_hint_minus_zero_heap_pushes']=[y-x for x,y in zip(targets['zero_heap_pushes'],targets['first_hint_heap_pushes'])];l=rank['expected_CHANNEL_span'];f=rank['manifest_fanout'];ll,ff,lf=dot(l,l),dot(f,f),dot(l,f);det=ll*ff-lf*lf
  for target,y in targets.items():
   yr=centered(y);yy=dot(yr,yr);yl,yf=dot(yr,l),dot(yr,f)
   for method in methods:
    row=next(x for x in r['rows'] if x['case']==case and x['target']==target and x['method']==method);xr=rank[method];xx,xy=dot(xr,xr),dot(xr,yr);rho=xy/math.sqrt(xx*yy) if xx and yy else None;assert (rho is None)==(row['spearman'] is None)
    if rho is not None:assert abs(rho-row['spearman'])<1e-12
    selected=heapq.nsmallest(K,range(len(ids)),key=lambda i:(-scores[method][i],ids[i]));boundary=min(scores[method][i] for i in selected);assert row['feature_boundary']==str(boundary) and row['feature_boundary_tie_size']==sum(x==boundary for x in scores[method])
    if target=='first_hint_minus_zero_heap_pushes':assert row['work_capture'] is None
    else:assert abs(row['work_capture']-sum(y[i] for i in selected)/sum(y))<1e-12
    expected=None
    if method=='expected_penalty_exposure' and det:
     xl,xf=dot(xr,l),dot(xr,f);vx=xx*det-xl*xl*ff+2*xl*xf*lf-xf*xf*ll;vy=yy*det-yl*yl*ff+2*yl*yf*lf-yf*yf*ll;cov=xy*det-xl*yl*ff+(xl*yf+xf*yl)*lf-xf*yf*ll;assert vx>=0 and vy>=0
     if vx and vy:expected=cov/math.sqrt(vx*vy)
    partial=row['exposure_partial_rank_controlling_fanout_and_expected_span'];assert (partial is None)==(expected is None)
    if partial is not None:max_error=max(max_error,abs(partial-expected));assert abs(partial-expected)<1e-9
    verified+=1
  bindings[str(ep)]=sha(ep);bindings[str(fp)]=sha(fp);print('CURRENT_NET_EXPOSURE_SCORES_VERIFIED',case,flush=True)
 assert verified==27;(O/'independent_verification_v1.json').open('x').write(json.dumps(dict(status='ALL27_CURRENT_NET_DIAGNOSTIC_RANK_CAPTURE_AND_PARTIAL_STATISTICS_VERIFIED',cells_verified=verified,max_partial_formula_error=max_error,bindings=bindings,scope='Independent full-domain descriptive statistic verification. No primary/native gate replacement, target-trained weights, causal policy benefit, unseen-family admission or full-workflow timing claim.'),indent=2)+'\n')
if __name__=='__main__':main()
