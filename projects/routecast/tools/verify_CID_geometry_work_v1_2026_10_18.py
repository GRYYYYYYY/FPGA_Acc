"""Independent exact group moments, rational ordering and heap-based selection."""
import array,collections,heapq,json,math,sys
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def ranks(v):
 order=sorted(range(len(v)),key=v.__getitem__);a=[0]*len(v);i=0
 while i<len(order):
  j=i+1
  while j<len(order) and v[order[j]]==v[order[i]]:j+=1
  for k in range(i,j):a[order[k]]=i+j-len(v)
  i=j
 return a

def main():
 E=R/'experiments';out=E/'mmc_CID_geometry_work_v1_2026-10-18';rp=out/'results.json';r=json.loads(rp.read_text());root=E/'mmc_endpoint_geometry_topology_v2_2026-10-18';plan=json.loads((root/'evaluation_protocol_v1.json').read_text());manifest=json.loads((root/'vector_manifest.json').read_text());work=json.loads((E/'mmc_native_connection_work_replay_v1_2026-10-18/verification.json').read_text());calls=json.loads((E/'mmc_native_connection_CID_binding_v1_2026-10-18/verification.json').read_text());cache={};checked=0;maxerror=0;undefined=0
 featureproof=json.loads((root/'independent_verification_v1.json').read_text());feature_receipt=json.loads((root/'receipt.json').read_text());assert sha(root/'vector_manifest.json')==featureproof['bindings'][str(root/'vector_manifest.json')]==plan['input_manifest_sha256'];assert sha(root/'receipt.json')==featureproof['bindings'][str(root/'receipt.json')]
 for folder in ['mmc_native_connection_CID_binding_v1_2026-10-18','mmc_native_connection_work_replay_v1_2026-10-18']:
  p=E/folder/'verification.json';proof=json.loads((E/folder/'independent_verification_v1.json').read_text());assert sha(p)==proof['bindings'][str(p)]
 for case in plan['cases']:
  p=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';assert sha(p)==feature_receipt['bindings'][str(p)]

 def read(d):
  if d['path'] not in cache:
   assert sha(d['path'])==d['sha256'];a=array.array(d['typecode']);a.frombytes(Path(d['path']).read_bytes());assert len(a)==115572 and sys.byteorder==d['byteorder'];cache[d['path']]=a
  return cache[d['path']]
 def correlation(x,y,groups):
  sums=collections.defaultdict(lambda:[0,0,0,0,0,0])
  for a,b,g in zip(x,y,groups):
   z=sums[g];z[0]+=1;z[1]+=a;z[2]+=b;z[3]+=a*a;z[4]+=b*b;z[5]+=a*b
  moments=[sum((F(z[0]*z[k]-z[j]*z[l],z[0]) for z in sums.values() if z[0]>1),F(0)) for k,j,l in [(3,1,1),(4,2,2),(5,1,2)]];xx,yy,xy=moments;assert min(xx,yy)>=0
  return float(xy)/math.sqrt(float(xx)*float(yy)) if xx and yy else None
 for case in plan['cases']:
  ep=json.loads((E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json').read_text());net={q['connection_id']:q['net_id'] for q in ep['connections']};assert set(net)==set(range(115572))
  for policy in plan['policies']:
   c=next(x for x in calls['rows'] if x['case']==case and x['arm']==policy)['vectors'];w=next(x for x in work['rows'] if x['case']==case and x['arm']==policy)['vectors'];success,failed=read(c['successful_sink_operations']),read(c['failed_sink_attempts']);attempts=[a+b for a,b in zip(success,failed)];heap={k:read(w[k]) for k in ['heap_pushes','heap_pops']};coverage=next(x for x in r['coverage'] if x['case']==case and x['policy']==policy);assert coverage['attempted_CIDs']==sum(x>0 for x in attempts) and coverage['zero_attempt_CIDs']==sum(x==0 for x in attempts) and coverage['total_attempts']==sum(attempts)
   for domain in ['all_CIDs_zero_for_no_attempt','attempted_CIDs_only']:
    ids=[i for i in range(115572) if domain.startswith('all_') or attempts[i]>0];N=len(ids);K=N//20;ng=[net[i] for i in ids];ag=[attempts[i] for i in ids];targets={}
    for target in plan['targets']:
     name=target.removeprefix('CID_').removesuffix('_per_attempt');raw=heap[name];y=[F(raw[i],attempts[i]) if attempts[i] else F(0) for i in ids] if target.endswith('_per_attempt') else [raw[i] for i in ids];targets[target]=(ranks(y),raw)
    for feature,direction in plan['scores'].items():
     a=read(manifest[case+'__'+feature]);sign=-1 if direction.startswith('smaller') else 1;x=[sign*a[i] for i in ids];xr=ranks(x);selected=heapq.nsmallest(K,range(N),key=lambda j:(-x[j],ids[j]));constant=min(x)==max(x)
     for target,(yr,raw) in targets.items():
      row=next(x for x in r['rows'] if x['case']==case and x['policy']==policy and x['domain']==domain and x['feature']==feature and x['target']==target);assert row['CIDs']==N and row['K']==K and row['constant_score']==constant
      for groups,field in [([0]*N,'spearman'),(ng,'within_NET_rank_correlation'),(ag,'within_exact_attempt_count_rank_correlation')]:
       actual=correlation(xr,yr,groups);expected=row[field];assert (actual is None)==(expected is None),(case,policy,feature,target,field,actual,expected)
       if actual is None:undefined+=1
       else:maxerror=max(maxerror,abs(actual-expected));assert abs(actual-expected)<1e-12
      capture=sum(raw[ids[j]] for j in selected)/sum(raw[i] for i in ids);assert capture==row['top5percent_total_heap_work_capture']
      if feature in ['source_outdegree','source_two_hop_unique']:assert row['within_NET_rank_correlation'] is None
      checked+=1
  print('INDEPENDENT CID GEOMETRY MATRIX PASS',case,flush=True)
 assert checked==336
 for p,h in r['bindings'].items():assert sha(p)==h
 summary={}
 for feature in plan['scores']:
  for target in ['CID_heap_pushes_per_attempt','CID_heap_pops_per_attempt']:
   a=[x for x in r['rows'] if x['domain']=='attempted_CIDs_only' and x['feature']==feature and x['target']==target];summary[feature+'__'+target]={}
   for field in ['spearman','within_NET_rank_correlation','within_exact_attempt_count_rank_correlation']:
    v=[x[field] for x in a if x[field] is not None];summary[feature+'__'+target][field]=[min(v),max(v)] if v else None
 bindings={str(p):sha(p) for p in [rp,Path(__file__),root/'evaluation_protocol_v1.json']}
 with (out/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all336_CID_feature_work_rank_capture_and_group_statistics_verified',bindings=bindings,cells_verified=checked,max_formula_error=maxerror,undefined_statistics_retained=undefined,attempted_CID_per_attempt_summary=summary,scope=plan['scope']),f,indent=2)
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
