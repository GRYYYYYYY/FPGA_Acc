"""All fixed diagnostic features/targets, complete NET domain, no policy gate."""
import pathlib,json,hashlib,array,math,sys
from collections import defaultdict
from fractions import Fraction
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def corr(a,b):
 d=dot(a,a)*dot(b,b);return dot(a,b)/math.sqrt(d) if d else None
def main():
 P=R/'experiments/mmc_current_NET_exposure_work_diagnostic_protocol_v1_2026-10-19/protocol.json';p=json.loads(P.read_text());F=R/'experiments/mmc_current_NET_exposure_features_v1_2026-10-19';fp=F/'receipt.json';fv=F/'independent_verification_v1.json';f=json.loads(fp.read_text());proof=json.loads(fv.read_text());assert proof['status']=='ALL3_INPUT_ONLY_NET_FEATURES_INDEPENDENTLY_VERIFIED';M=R/'experiments/mmc_first_hint_connection_work_replay_v1_2026-10-19';mp=M/'verification.json';vp=M/'independent_verification_v1.json';measured=json.loads(mp.read_text());v=json.loads(vp.read_text());assert v['status']=='ALL6_CURRENT_CID_IDENTITY_SNAPSHOT_ARITHMETIC_AND_FULL_VECTORS_INDEPENDENTLY_VERIFIED';O=R/'experiments/mmc_current_NET_exposure_work_diagnostic_v1_2026-10-19';O.mkdir(exist_ok=False);bindings={str(x):sha(x) for x in [P,fp,fv,mp,vp,pathlib.Path(__file__).resolve(),R/'tools/verify_mmc_pressure_risk_v2_2026_10_18.py']};rows=[]
 for plan in p['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());members=defaultdict(list)
  for q in meta['connections']:members[q['net_id']].append(q['connection_id'])
  ids=sorted(members);assert len(ids)==55300;K=len(ids)//20;features=pathlib.Path(next(x for x in f['cases'] if x['case']==case)['features']);assert proof['bindings'][str(features)]==sha(features);data=[json.loads(l) for l in features.read_text().splitlines()];assert [x['net_id'] for x in data]==ids;scores={method:[Fraction(x[method]) for x in data] for method in p['methods']};ranks={k:rank_info(x,K) for k,x in scores.items()};targets={}
  for arm,name in [('zero','zero_heap_pushes'),('forecast','first_hint_heap_pushes')]:
   row=next(x for x in measured['rows'] if x['case']==case and x['arm']==arm);desc=row['vectors']['heap_pushes'];path=pathlib.Path(desc['path']);assert sha(path)==desc['sha256']==v['bindings'][str(path)] and desc['byteorder']==sys.byteorder;values=array.array('Q');values.frombytes(path.read_bytes());assert len(values)==115572;targets[name]=[sum(values[c] for c in members[n]) for n in ids];assert sum(targets[name])==row['native_heap_pushes'];bindings[str(path)]=sha(path)
  targets['first_hint_minus_zero_heap_pushes']=[b-a for a,b in zip(targets['zero_heap_pushes'],targets['first_hint_heap_pushes'])];l=ranks['expected_CHANNEL_span']['center'];fan=ranks['manifest_fanout']['center'];ll,ff,lf=dot(l,l),dot(fan,fan),dot(l,fan);det=ll*ff-lf*lf
  def residual(x):
   if not det:return None
   xl,xf=dot(x,l),dot(x,fan);a=Fraction(xl*ff-xf*lf,det);b=Fraction(xf*ll-xl*lf,det);z=[Fraction(t)-a*u-b*w for t,u,w in zip(x,l,fan)];return z if any(z) else None
  xres=residual(ranks['expected_penalty_exposure']['center'])
  for target,y in targets.items():
   yr=rank_info(y,K);yres=residual(yr['center']);partial=corr(xres,yres) if xres is not None and yres is not None else None
   for method,score in scores.items():
    xr=ranks[method];selected=xr['selected'];row=dict(case=case,method=method,target=target,NETs=len(ids),K=K,spearman=corr(xr['center'],yr['center']),exposure_partial_rank_controlling_fanout_and_expected_span=partial if method=='expected_penalty_exposure' else None,work_capture=(sum(y[i] for i in selected)/sum(y) if target!='first_hint_minus_zero_heap_pushes' else None),feature_boundary=str(xr['boundary']),feature_boundary_tie_size=xr['equal']);rows.append(row)
  for x in [ep,features]:bindings[str(x)]=sha(x)
  print('NET_EXPOSURE_DIAGNOSTIC_SCORED',case,flush=True)
 assert len(rows)==27;result=dict(status='ALL27_FIXED_CURRENT_NET_EXPOSURE_DIAGNOSTIC_CELLS_COMPUTED',rows=rows,bindings=bindings,scope='Posthoc complete current development NET work association, all fixed methods/targets/cases retained. Signed work delta has Spearman only, no invalid signed capture. Conditional rank association is not prediction-weight fitting or causal evidence. Original policy/prediction/utility gates unchanged, independent scoring verification pending.')
 (O/'results.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
