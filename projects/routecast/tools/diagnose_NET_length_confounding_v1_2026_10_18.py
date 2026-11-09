"""Post-hoc exposed-data diagnostics, standard-library implementation."""
import sys,json,itertools,math,array
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def rank(values):
 order=sorted(range(len(values)),key=values.__getitem__);result=[0.0]*len(values);i=0
 while i<len(values):
  j=i+1
  while j<len(values) and values[order[j]]==values[order[i]]:j+=1
  for k in range(i,j):result[order[k]]=(i+j-1)/2
  i=j
 return result

def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def center(a):
 mean=math.fsum(a)/len(a);return [x-mean for x in a]
def corr(a,b):
 a,b=center(a),center(b);den=math.sqrt(dot(a,a)*dot(b,b));return dot(a,b)/den if den else None
def residual(a,l):
 a=center(a);weight=dot(a,l)/dot(l,l);return [x-weight*y for x,y in zip(a,l)]
def grouped(a,groups):
 values={}
 for x,g in zip(a,groups):values.setdefault(g,[]).append(x)
 means={g:math.fsum(v)/len(v) for g,v in values.items()};return [x-means[g] for x,g in zip(a,groups)]

def main():
 src=R/'experiments/mmc_NET_pressure_exposure_v1_2026-10-18/vector_manifest.json';target=R/'experiments/mmc_NET_pressure_targets_v1_2026-10-18/vector_manifest.json';proof=R/'experiments/mmc_NET_pressure_inputs_verification_v1_2026-10-18/verification.json';sv=json.loads(src.read_text());tv=json.loads(target.read_text());verified=json.loads(proof.read_text());out=R/'experiments/mmc_NET_length_confounding_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [src,target,proof,Path(__file__)]};rows=[]
 def read(manifest,key,typecode):
  v=manifest[key];p=Path(v['path']);assert sha(p)==v['sha256'];assert verified['bindings'][str(p)]==v['sha256'];bindings[str(p)]=v['sha256'];a=array.array(typecode);a.frombytes(p.read_bytes());assert sys.byteorder=='little' and a.itemsize==8 and len(a)==55300 and all(math.isfinite(x) for x in a);return a
 for case,source in itertools.product(['case_01','case_02','case_03'],['raw_min_off','raw_min_on','native_retained_off','native_retained_on','previous_native','native_retained_terminal_batch']):
  length=read(sv,f'{case}__{source}__unique_node_count','d');assert all(x==int(x) for x in length);lr=rank(length);lc=center(lr)
  for policy in ['off','on']:
   y=read(tv,f'{case}__{policy}__total_successful_NET_route_operations','Q');yr=rank(y);yrres=residual(yr,lc);yg=grouped(yr,length)
   for method in ['anchored_risk_sum','uniform_risk_sum']:
    x=read(sv,f'{case}__{source}__{method}','d');xr=rank(x);xrres=residual(xr,lc);xy=corr(xr,yr);xl=corr(xr,lr);yl=corr(yr,lr);partial=corr(xrres,yrres);formula=(xy-xl*yl)/math.sqrt((1-xl*xl)*(1-yl*yl));assert abs(partial-formula)<1e-11;within=corr(grouped(xr,length),yg)
    rows.append(dict(case=case,source=source,policy=policy,method=method,spearman=xy,score_length_spearman=xl,length_target_spearman=yl,partial_rank_correlation_controlling_linear_length_rank=partial,pooled_rank_correlation_after_exact_length_group_mean_removal=within))
 for p,h in bindings.items():assert sha(p)==h
 with (out/'results.json').open('x') as f:json.dump(dict(status='all72_development_length_confounding_diagnostics_complete',bindings=bindings,rows=rows,scope='Post-hoc exposed whole-NET operation counts. Partial rank correlation removes linear length-rank projection; pooled exact-length residual statistic removes group rank means. Not all confounders, causal evidence, independent validation or per-NET timing. Original primary/gates unchanged.'),f,indent=2)
 print(json.dumps([r for r in rows if r['source']=='native_retained_on'],indent=2))
if __name__=='__main__':main()
