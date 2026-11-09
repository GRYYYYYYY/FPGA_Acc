"""Independent integer-rank/covariance verification of all72diagnostics."""
import sys,json,array,math,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from verify_mmc_pressure_risk_v2_2026_10_18 import rank_info

def main():
 d=R/'experiments/mmc_NET_length_confounding_v1_2026-10-18';rp=d/'results.json';r=json.loads(rp.read_text());sv=json.loads((R/'experiments/mmc_NET_pressure_exposure_v1_2026-10-18/vector_manifest.json').read_text());tv=json.loads((R/'experiments/mmc_NET_pressure_targets_v1_2026-10-18/vector_manifest.json').read_text());cache={}
 def data(key,target=False):
  desc=(tv if target else sv)[key];p=desc['path']
  if p not in cache:
   a=array.array('Q' if target else 'd');a.frombytes(Path(p).read_bytes());assert sha(p)==desc['sha256'];cache[p]=(a,rank_info(a,1)['center'])
  return cache[p]
 def dot(a,b):return sum(x*y for x,y in zip(a,b))
 def rho(a,b):return dot(a,b)/math.sqrt(dot(a,a)*dot(b,b))
 for row in r['rows']:
  prefix=row['case']+'__'+row['source']+'__';length,l=data(prefix+'unique_node_count');_,x=data(prefix+row['method']);_,y=data(row['case']+'__'+row['policy']+'__total_successful_NET_route_operations',True);xy,xl,yl=rho(x,y),rho(x,l),rho(y,l);partial=(xy-xl*yl)/math.sqrt((1-xl*xl)*(1-yl*yl));groups=collections.defaultdict(lambda:[0,0,0])
  for g,a,b in zip(length,x,y):v=groups[g];v[0]+=1;v[1]+=a;v[2]+=b
  cov=dot(x,y)-math.fsum(a*b/n for n,a,b in groups.values());vx=dot(x,x)-math.fsum(a*a/n for n,a,b in groups.values());vy=dot(y,y)-math.fsum(b*b/n for n,a,b in groups.values());within=cov/math.sqrt(vx*vy)
  for key,value in [('spearman',xy),('partial_rank_correlation_controlling_linear_length_rank',partial),('pooled_rank_correlation_after_exact_length_group_mean_removal',within)]:assert abs(row[key]-value)<1e-11
 for p,h in r['bindings'].items():assert sha(p)==h
 fixed=[x for x in r['rows'] if x['source']=='native_retained_on'];index={(x['case'],x['policy'],x['method']):x for x in fixed};key='partial_rank_correlation_controlling_linear_length_rank';wins=sum(index[c,p,'uniform_risk_sum'][key]>index[c,p,'anchored_risk_sum'][key] for c in ['case_01','case_02','case_03'] for p in ['off','on']);result=dict(status='all72_rank_partial_and_exact_length_residual_statistics_verified',bindings={str(p):sha(p) for p in [rp,Path(__file__),R/'tools/verify_mmc_pressure_risk_v2_2026_10_18.py']},fixed_primary_source_uniform_partial_higher_pairs=wins,fixed_source_partial_ranges={m:[min(x[key] for x in fixed if x['method']==m),max(x[key] for x in fixed if x['method']==m)] for m in ['anchored_risk_sum','uniform_risk_sum']},decision='Length alone does not explain this exposed association. Uniform control remains stronger under both controls for fixed primary source; retain prior no-policy-promotion decision. Partial correlation is not causal evidence, native intervention or independent family validation.')
 with (d/'verification_v1.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
