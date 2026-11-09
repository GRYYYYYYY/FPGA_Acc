"""Execute fixed signed endpoint-feature versus actual CID work diagnostic."""
import array,collections,json,math,sys
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from diagnose_NET_length_confounding_v1_2026_10_18 import rank

def doubled(v):return [int(2*x-len(v)+1) for x in rank(v)]
def corr(x,y,groups=None):
 xx=sum(a*a for a in x);yy=sum(b*b for b in y);xy=sum(a*b for a,b in zip(x,y))
 if groups is not None:
  sums=collections.defaultdict(lambda:[0,0,0])
  for g,a,b in zip(groups,x,y):s=sums[g];s[0]+=1;s[1]+=a;s[2]+=b
  xx=F(xx)-sum((F(a*a,n) for n,a,b in sums.values()),F(0));yy=F(yy)-sum((F(b*b,n) for n,a,b in sums.values()),F(0));xy=F(xy)-sum((F(a*b,n) for n,a,b in sums.values()),F(0))
 assert xx>=0 and yy>=0
 return float(xy)/math.sqrt(float(xx)*float(yy)) if xx and yy else None

def main():
 E=R/'experiments';out=E/'mmc_CID_geometry_work_v1_2026-10-18';out.mkdir(exist_ok=False);src=E/'mmc_endpoint_geometry_topology_v2_2026-10-18';bindings={};cache={}
 def load(p):
  p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 plan=load(src/'evaluation_protocol_v1.json');manifest=load(src/'vector_manifest.json');assert sha(src/'vector_manifest.json')==plan['input_manifest_sha256'];fp=load(src/'independent_verification_v1.json');assert fp['feature_values_verified']==2427012;work=load(E/'mmc_native_connection_work_replay_v1_2026-10-18/verification.json');wp=load(E/'mmc_native_connection_work_replay_v1_2026-10-18/independent_verification_v1.json');calls=load(E/'mmc_native_connection_CID_binding_v1_2026-10-18/verification.json');cp=load(E/'mmc_native_connection_CID_binding_v1_2026-10-18/independent_verification_v1.json');bindings[str(Path(__file__))]=sha(__file__);helper=R/'tools/diagnose_NET_length_confounding_v1_2026_10_18.py';bindings[str(helper)]=sha(helper)
 def read(d,proof=None):
  p=d['path']
  if proof is not None:assert proof['bindings'][p]==d['sha256']
  if p not in cache:
   assert sha(p)==d['sha256'];a=array.array(d['typecode']);a.frombytes(Path(p).read_bytes());assert len(a)==115572 and sys.byteorder==d['byteorder'];cache[p]=a;bindings[p]=d['sha256']
  return cache[p]
 rows=[];coverage=[]
 for case in plan['cases']:
  ep=load(E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json');qs=sorted(ep['connections'],key=lambda q:q['connection_id']);assert [q['connection_id'] for q in qs]==list(range(115572));nets=[q['net_id'] for q in qs];scores={name:[(-1 if direction.startswith('smaller') else 1)*x for x in read(manifest[case+'__'+name])] for name,direction in plan['scores'].items()}
  for policy in plan['policies']:
   c=next(x for x in calls['rows'] if x['case']==case and x['arm']==policy)['vectors'];w=next(x for x in work['rows'] if x['case']==case and x['arm']==policy)['vectors'];s,f=read(c['successful_sink_operations'],cp),read(c['failed_sink_attempts'],cp);attempts=[a+b for a,b in zip(s,f)];heap={name:read(w[name],wp) for name in ['heap_pushes','heap_pops']};assert all(a or (heap['heap_pushes'][i]==heap['heap_pops'][i]==0) for i,a in enumerate(attempts));coverage.append(dict(case=case,policy=policy,CIDs=115572,attempted_CIDs=sum(n>0 for n in attempts),zero_attempt_CIDs=sum(n==0 for n in attempts),total_attempts=sum(attempts)))
   for domain in ['all_CIDs_zero_for_no_attempt','attempted_CIDs_only']:
    ids=[i for i,n in enumerate(attempts) if domain.startswith('all_') or n];N=len(ids);K=N//20;ng=[nets[i] for i in ids];ag=[attempts[i] for i in ids];targets={}
    for name,values in heap.items():
     targets['CID_'+name]=[values[i] for i in ids];targets['CID_'+name+'_per_attempt']=[F(values[i],attempts[i]) if attempts[i] else F(0) for i in ids]
    ranked={t:doubled(y) for t,y in targets.items()}
    for feature,values in scores.items():
     x=[values[i] for i in ids];xr=doubled(x);selected=sorted(range(N),key=lambda j:(-x[j],ids[j]))[:K]
     for target,y in targets.items():
      yr=ranked[target];rawname=target.removeprefix('CID_').removesuffix('_per_attempt');raw=heap[rawname];capture=sum(raw[ids[j]] for j in selected)/sum(raw[i] for i in ids);rows.append(dict(case=case,policy=policy,domain=domain,feature=feature,target=target,CIDs=N,K=K,spearman=corr(xr,yr),within_NET_rank_correlation=corr(xr,yr,ng),within_exact_attempt_count_rank_correlation=corr(xr,yr,ag),top5percent_total_heap_work_capture=capture,constant_score=len(set(x))==1))
  print('CID GEOMETRY WORK MATRIX CASE',case,flush=True)
 assert len(rows)==336
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all336_fixed_signed_CID_geometry_work_cells_computed',bindings=bindings,coverage=coverage,rows=rows,scope=plan['scope'],independent_verification_pending=True),f,indent=2)
if __name__=='__main__':main()
