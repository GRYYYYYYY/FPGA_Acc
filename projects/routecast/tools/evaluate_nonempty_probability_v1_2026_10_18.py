"""Retrospective binary-label probability diagnostic; all existing gates retained."""
import sys,json,array,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';gp=E/'mmc_typed_collision_risk_v1_2026-10-18/groups.json';g=json.loads(gp.read_text());nodes=sorted(n for group in g['groups'] if group['kind']=='geometry_channel' for n in group['members']);assert len(nodes)==258720;index={n:i for i,n in enumerate(g['positive_RR_ids'])};indices=[index[n] for n in nodes]
 srcs=[('uniform','mmc_typed_collision_risk_v1_2026-10-18','typed_group_mean','typed_NET_collision','mmc_typed_collision_risk_verification_v1_2026-10-18'),('anchored','mmc_anchored_NET_forecasts_v1_2026-10-18','anchored_group_mean','anchored_NET_collision','mmc_anchored_NET_forecasts_verification_v1_2026-10-18')];plan=json.loads((E/'mmc_anchored_NET_forecasts_v1_2026-10-18/protocol.json').read_text());out=E/'mmc_nonempty_probability_v1_2026-10-18';out.mkdir(exist_ok=False);(out/'vectors').mkdir();bindings={str(p):sha(p) for p in [Path(__file__),gp]};manifest={};means={}
 protocol=dict(rule='p=E[U]-E[(U-1)+]=P(U>0) for unit-capacity channel resources; arithmetic from independently admitted float64 expectations, clamp only boundary roundoff<=1e-12.',scope='Retrospective exposed development cold binary targets. No tuning, mixture selection, target-dependent parameter, independent-test claim or replacement of original four-metric cold/native gates. Probability refers to source NET-choice prior, not repaired final routes.',cases=plan['cases'],sources=plan['sources'])
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2))
 for method,sub,meanname,riskname,proofsub in srcs:
  mp=E/sub/'vector_manifest.json';m=json.loads(mp.read_text());pp=E/proofsub/'verification.json';proof=json.loads(pp.read_text());bindings[str(mp)]=sha(mp);bindings[str(pp)]=sha(pp)
  for case in plan['cases']:
   for source in plan['sources']:
    vectors=[]
    for name in [meanname,riskname]:
     v=m[case+'__'+source+'__'+name];assert sha(v['path'])==v['sha256']==proof['bindings'][v['path']];a=array.array('d');a.frombytes(Path(v['path']).read_bytes());assert len(a)==904438;vectors.append(a);bindings[v['path']]=v['sha256']
    mean,risk=vectors;prob=array.array('d');clipped=array.array('d')
    for i in indices:
     p=mean[i]-risk[i];assert -1e-12<=p<=1+1e-12;prob.append(min(1,max(0,p)));clipped.append(min(1,max(0,mean[i])))
    key=case+'__'+source+'__'+method;p=out/'vectors'/(key+'.f64');p.write_bytes(prob.tobytes());manifest[key]=dict(path=str(p),sha256=sha(p),values=len(prob));means[key]=clipped
 # Seal all source-derived output vectors before loading target labels.
 (out/'vector_manifest.json').write_text(json.dumps(manifest,indent=2));rows=[]
 for case in plan['cases']:
  vp=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/vectors.json';proof=json.loads(vp.with_name('verification.json').read_text());assert sha(vp)==proof['bindings'][str(vp)];v=json.loads(vp.read_text())['channels'];truthmap={r['node']:r['labels']['cold'] for r in v};truth=[truthmap[n] for n in nodes];assert all(y in [0,1] for y in truth);bindings[str(vp)]=sha(vp)
  for source in plan['sources']:
   for method,_,_,_,_ in srcs:
    key=case+'__'+source+'__'+method;prob=array.array('d');prob.frombytes(Path(manifest[key]['path']).read_bytes());mean=means[key]
    def score(a):return dict(Brier=math.fsum((x-y)**2 for x,y in zip(a,truth))/len(truth),MAE=math.fsum(abs(x-y) for x,y in zip(a,truth))/len(truth),predicted_mass=math.fsum(a))
    bins=[dict(count=0,predicted=0.,positive=0) for _ in range(10)]
    for p,y in zip(prob,truth):b=bins[min(9,int(p*10))];b['count']+=1;b['predicted']+=p;b['positive']+=y
    rows.append(dict(case=case,source=source,method=method,nonempty_probability=score(prob),clipped_mean_control=score(mean),cold_mass=sum(truth),calibration_bins=bins))
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all36_nonempty_probability_diagnostics_computed',bindings=bindings,rows=rows,scope=protocol['scope']),f,indent=2)
 print(json.dumps([r for r in rows if r['source']=='native_retained_on'],indent=2))
if __name__=='__main__':main()
