"""Independent doubled ranks and exact rational within-count covariance checks."""
import array,collections,hashlib,json,math,sys
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ranks(v):
 order=sorted(range(len(v)),key=lambda i:(v[i],i));a=[0]*len(v);i=0
 while i<len(v):
  j=i+1
  while j<len(v) and v[order[j]]==v[order[i]]:j+=1
  for k in range(i,j):a[order[k]]=i+j-len(v)
  i=j
 return a
def main():
 E=R/'experiments';out=E/'mmc_NET_heap_per_attempt_v2_2026-10-18';rp=out/'results.json';r=json.loads(rp.read_text());src=E/'mmc_NET_pressure_exposure_v1_2026-10-18';sm=json.loads((src/'vector_manifest.json').read_text());dom=json.loads((src/'NET_domains.json').read_text());calls=json.loads((E/'mmc_native_connection_CID_binding_v1_2026-10-18/verification.json').read_text());work=json.loads((E/'mmc_native_connection_work_replay_v1_2026-10-18/verification.json').read_text());cache={};checked=0;error=0
 def read(desc):
  p=desc['path']
  if p not in cache:
   assert sha(p)==desc['sha256'];a=array.array(desc.get('typecode','d'));a.frombytes(Path(p).read_bytes());assert len(a)==desc['values'] and sys.byteorder=='little';cache[p]=a
  return cache[p]
 def rho(xy,xx,yy):return float(xy)/math.sqrt(float(xx)*float(yy)) if xx>0 and yy>0 else None
 def check(a,b):
  nonlocal error
  assert (a is None)==(b is None),(a,b)
  if a is not None:error=max(error,abs(a-b));assert abs(a-b)<1e-9,(a,b)
 for case in ['case_01','case_02','case_03']:
  ep=json.loads((E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json').read_text());ids=dom[case]['NET_ids'];members=collections.defaultdict(list)
  for q in ep['connections']:members[q['net_id']].append(q['connection_id'])
  assert ids==sorted(members);fan=[len(members[n]) for n in ids]
  for policy in ['off','on']:
   cv=next(x for x in calls['rows'] if x['case']==case and x['arm']==policy)['vectors'];wv=next(x for x in work['rows'] if x['case']==case and x['arm']==policy)['vectors'];s=read(cv['successful_sink_operations']);f=read(cv['failed_sink_attempts']);attempts=[sum(s[i]+f[i] for i in members[n]) for n in ids];heap={k:[sum(read(wv[k])[i] for i in members[n]) for n in ids] for k in ['heap_pushes','heap_pops']};coverage=next(x for x in r['coverage'] if x['case']==case and x['policy']==policy);assert coverage['attempted_NETs']==sum(x>0 for x in attempts) and coverage['zero_attempt_NETs']==sum(x==0 for x in attempts) and coverage['successful_attempts']==sum(s) and coverage['failed_attempts']==sum(f)
   for domain in ['all_NETs_zero_for_no_attempt','attempted_NETs_only']:
    selected=[i for i,n in enumerate(attempts) if domain.startswith('all_') or n];groups=[attempts[i] for i in selected];sizes=collections.Counter(groups);vectors={};gsums={};memo={}
    def add(key,values):
     a=ranks(values);vectors[key]=a;sums=collections.Counter()
     for g,v in zip(groups,a):sums[g]+=v
     gsums[key]=sums
    def cov(a,b,within):
     key=(min(a,b),max(a,b),within)
     if key not in memo:
      n=sum(x*y for x,y in zip(vectors[a],vectors[b]));memo[key]=F(n)-sum((F(gsums[a][g]*gsums[b][g],size) for g,size in sizes.items()),F(0)) if within else F(n)
     return memo[key]
    add('fan',[fan[i] for i in selected])
    for name,values in heap.items():add(name,[F(values[i],attempts[i]) if attempts[i] else F(0) for i in selected])
    subset=[x for x in r['rows'] if x['case']==case and x['policy']==policy and x['domain']==domain]
    for source in sorted({x['source'] for x in subset}):
     for method in sorted({x['method'] for x in subset}):
      if method!='manifest_fanout':add(source+'__'+method,[read(sm[case+'__'+source+'__'+method])[i] for i in selected])
     l=source+'__unique_node_count'
     for row in [x for x in subset if x['source']==source]:
      x='fan' if row['method']=='manifest_fanout' else source+'__'+row['method'];y=row['target'].removesuffix('_per_attempt');assert row['NETs']==len(selected)
      for within,field in [(False,'spearman'),(True,'within_exact_attempt_count_rank_correlation')]:check(rho(cov(x,y,within),cov(x,x,within),cov(y,y,within)),row[field])
      expected=row['within_count_partial_rank_controlling_length_fanout']
      if row['method'] in ['manifest_fanout','unique_node_count']:assert expected is None
      else:
       ll,ff,lf=cov(l,l,True),cov('fan','fan',True),cov(l,'fan',True);det=ll*ff-lf*lf
       if det<=0:actual=None
       else:
        xx,yy,xy=cov(x,x,True),cov(y,y,True),cov(x,y,True);xl,xf,yl,yf=cov(x,l,True),cov(x,'fan',True),cov(y,l,True),cov(y,'fan',True);vx=xx*det-xl*xl*ff+2*xl*xf*lf-xf*xf*ll;vy=yy*det-yl*yl*ff+2*yl*yf*lf-yf*yf*ll;cross=xy*det-xl*yl*ff+(xl*yf+xf*yl)*lf-xf*yf*ll;assert vx>=0 and vy>=0;actual=rho(cross,vx,vy)
       check(actual,expected)
      checked+=1
  print('INDEPENDENT PER ATTEMPT CASE PASS',case,flush=True)
 assert checked==864
 for p,h in r['bindings'].items():assert sha(p)==h
 summary={}
 for method in ['anchored_risk_sum','uniform_risk_sum']:
  for target in ['heap_pushes_per_attempt','heap_pops_per_attempt']:
   a=[x for x in r['rows'] if x['source']=='native_retained_on' and x['method']==method and x['target']==target and x['domain']=='attempted_NETs_only'];summary[method+'__'+target]={field:[min(x[field] for x in a),max(x[field] for x in a)] for field in ['spearman','within_exact_attempt_count_rank_correlation','within_count_partial_rank_controlling_length_fanout']}
 bindings={str(p):sha(p) for p in [rp,out/'protocol.json',Path(__file__)]}
 with (out/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all864_per_attempt_rational_targets_and_exact_covariance_statistics_verified',bindings=bindings,cells_verified=checked,max_formula_error=error,fixed_primary_source_attempted_NET_summary=summary,scope='Outcome-derived count conditioning and active-subset analyses are descriptive only. No unseen-family, elapsed-time or original utility/quality gate claim.'),f,indent=2)
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
