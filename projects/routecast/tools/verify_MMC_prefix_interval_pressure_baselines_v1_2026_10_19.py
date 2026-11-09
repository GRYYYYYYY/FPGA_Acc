"""Independent admitted XML-domain, feature provenance, grouped capture and ranks."""
import pathlib,json,hashlib,math,sys
from collections import Counter,defaultdict
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pressure_prefix_feature_contract_v1 import load as load_feature
from pressure_prefix_interval_contract_v1 import load as load_intervals
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def rho(x,y):
 n=len(x);joint=Counter(zip(x,y));cx=Counter(x);cy=Counter(y)
 def rank(c):
  before=0;out={}
  for v,num in sorted(c.items()):out[v]=2*before+num-1;before+=num
  return out
 rx,ry=rank(cx),rank(cy);sx=sum(c*rx[v] for v,c in cx.items());sy=sum(c*ry[v] for v,c in cy.items());xx=n*sum(c*rx[v]**2 for v,c in cx.items())-sx*sx;yy=n*sum(c*ry[v]**2 for v,c in cy.items())-sy*sy;xy=n*sum(c*rx[u]*ry[v] for (u,v),c in joint.items())-sx*sy
 return xy/math.sqrt(xx*yy) if xx and yy else None

def main():
 out=R/'experiments/mmc_prefix_interval_pressure_baselines_v1_2026-10-19';r=json.loads((out/'results.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');domain=json.loads((out/'channel_domain.json').read_text());assert r['domain_sha256']==sha(out/'channel_domain.json');old=R/'experiments/mmc_atomic_pair_quality_v1_2026-10-18/case_01';audit=json.loads((old/'verification.json').read_text());assert audit['status']=='pass' and audit['complete_original_XML_positive_channel_and_span_domains_equal'];source=old/'vectors.json';assert audit['bindings'][str(source)]==sha(source);assert domain==sorted(x['node'] for x in json.loads(source.read_text())['channels']);ep=json.loads(pathlib.Path(p['endpoint']).read_text());graph=ep['inputs']['graph']['path'];assert audit['bindings'][graph]==p['bindings'][graph]
 splitroot=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';split=json.loads((splitroot/'verification.json').read_text());lookup={(x['case'],x['policy']):x for x in split['cases']};bindings={str(f):sha(f) for f in [pathlib.Path(__file__).resolve(),out/'results.json',out/'protocol.json',out/'channel_domain.json',old/'verification.json',source,splitroot/'verification.json']};count=0;cases=[]
 for row in r['cases']:
  case,policy=row['case'],row['policy'];entry=lookup[case,policy];folder=splitroot/f'{case}_{policy}';first=load_feature(folder/'features.json',entry['feature_sha256']);pp=out/f'{case}_{policy}_prediction.json';assert sha(pp)==row['prediction_sha256'];payload=json.loads(pp.read_text());prediction=payload['predictions']['prefix_overflow'];assert prediction==[first.get(n,0) for n in domain];mp=R/f'experiments/mmc_first_checkpoint_occupancy_bounds_v1_2026-10-19/{case}_{policy}/features.json';ip=mp.parent.parent/'verification.json';iv=json.loads(ip.read_text());assert p['bindings'][str(ip)]==sha(ip) and iv['bindings'][str(mp)]==p['bindings'][str(mp)];caps,intervals=load_intervals(mp,p['bindings'][str(mp)]);assert all(caps[n]==1 for n in domain);lower=payload['predictions']['capacity_lower_bound'];assert lower==[intervals['lower_occupancy'][n] for n in domain];targetfile=folder/'targets.json';assert sha(targetfile)==entry['target_sha256']==p['bindings'][str(targetfile)];targets=json.loads(targetfile.read_text());assert targets['first_target_iteration']==2
  for name,raw in targets['targets'].items():
   truth={int(n):v for n,v in raw.items()};t=[truth.get(n,0) for n in domain];total=sum(t)
   for method,values in [('capacity_lower_bound',lower),('prefix_overflow',prediction),('uniform_risk',[1]*len(domain))]:
    m=row['metrics'][name][method];k=len(domain)//20;groups=defaultdict(list)
    for score,target in zip(values,t):groups[score].append(target)
    remaining=k;mass=Fraction(0)
    for score,weights in sorted(groups.items(),reverse=True):
     take=min(remaining,len(weights));mass+=Fraction(take*sum(weights),len(weights));remaining-=take
     if remaining==0:break
    assert mass/total==Fraction(m['tie_averaged_mass_capture']);rr=rho(values,t);assert rr==m['spearman'] if rr is None else abs(rr-m['spearman'])<1e-12;assert m['full_domain_target_mass']==total and m['total_target_mass_all_RR']==sum(truth.values());assert Fraction(m['uniform_expected_mass_capture'])==Fraction(k,len(domain));count+=1
  metric=row['metrics']['sum_checkpoint_overflow_units']['capacity_lower_bound'];cases.append({'case':case,'policy':policy,'primary_capture':float(Fraction(metric['tie_averaged_mass_capture'])),'enrichment':metric['enrichment_over_uniform']});bindings[str(pp)]=sha(pp);bindings[str(targetfile)]=sha(targetfile)
 assert count==54;v=dict(status='all54_interval_rank_and_grouped_capture_vectors_and_full_domain_verified',bindings=bindings,cases=cases,independent_metric_vectors=count,scope='Independent exposed-data temporal baseline audit only. Uniform tie averaging belongs to this separately frozen diagnostic, not replacement original cold gates. No trained/generalized predictor, route intervention or complete-cost gain.',accepted_gain=False,strict_unseen_admitted=False);(out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(count,flush=True)
if __name__=='__main__':main()
