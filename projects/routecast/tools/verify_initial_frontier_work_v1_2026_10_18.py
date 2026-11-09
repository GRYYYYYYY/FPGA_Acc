"""Independent integer ranks, rational group moments and all72fixed cells."""
import collections,itertools,json,math,struct,sys
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from verify_CID_geometry_work_v1_2026_10_18 import ranks
MAX=2**64-1

def main():
 E=R/'experiments';out=E/'mmc_initial_frontier_work_v1_2026-10-18';rp=out/'results.json';r=json.loads(rp.read_text());src=E/'mmc_initial_frontier_replay_v1_2026-10-18';source=json.loads((src/'verification.json').read_text());pp=E/'mmc_native_connection_seed_phase_v1_2026-10-18/frontier_geometry_analysis_protocol_v1.json';plan=json.loads(pp.read_text());keys={(x['case'],x['policy'],x['domain'],x['feature'],x['target']) for x in r['rows']};assert len(r['rows'])==72 and keys==set(itertools.product(plan['cases'],plan['policies'],plan['domains'],plan['features'],plan['targets']));checked=0;maxerror=0
 def correlation(a,b,groups):
  sums=collections.defaultdict(lambda:[0,0,0,0,0,0])
  for x,y,g in zip(a,b,groups):
   s=sums[g];s[0]+=1;s[1]+=x;s[2]+=y;s[3]+=x*x;s[4]+=y*y;s[5]+=x*y
  moments=[sum((F(s[0]*s[k]-s[i]*s[j],s[0]) for s in sums.values() if s[0]>1),F(0)) for k,i,j in [(3,1,1),(4,2,2),(5,1,2)]];xx,yy,xy=moments;assert xx>=0 and yy>=0;return float(xy)/math.sqrt(float(xx)*float(yy)) if xx and yy else None
 for case,policy in itertools.product(plan['cases'],plan['policies']):
  desc=next(x for x in source['rows'] if x['case']==case and x['arm']==policy)['frontier_file'];assert sha(desc['path'])==desc['sha256'];records=[]
  with open(desc['path'],'rb') as f:
   assert f.readline()==b'RC_INITIAL_FRONTIER_LE64 1\n'
   while block:=f.read(96*(1<<14)):
    assert len(block)%96==0;records.extend(struct.iter_unpack('<12Q',block))
  coverage=next(x for x in r['coverage'] if x['case']==case and x['policy']==policy);assert coverage['attempts']==len(records)==desc['records'] and coverage['undefined_initial_gap']==sum(z[5]==MAX for z in records)
  for domain in plan['domains']:
   mode=None if domain.startswith('all_') else 0 if domain.startswith('normal_') else 1;data=[z for z in records if z[5]!=MAX and (mode is None or z[2]==mode)];cid=[z[1] for z in data];size=[z[4] for z in data];features={'initial_min_same_layer_L1':ranks([z[5] for z in data]),'source_sink_L1':ranks([z[6] for z in data])};targets={'remaining_heap_pushes_after_initial_seed_inserts':ranks([z[7]-z[3] for z in data]),'total_heap_pops':ranks([z[8] for z in data])};assert all(z[7]>=z[3] for z in data)
   for feature,x in features.items():
    for target,y in targets.items():
     row=next(v for v in r['rows'] if (v['case'],v['policy'],v['domain'],v['feature'],v['target'])==(case,policy,domain,feature,target));assert row['attempts']==len(data)
     for groups,field in [([0]*len(data),'spearman'),(cid,'within_CID_rank_correlation'),(size,'within_exact_initial_unique_seed_count_rank_correlation')]:
      actual=correlation(x,y,groups);expected=row[field];assert (actual is None)==(expected is None)
      if actual is not None:maxerror=max(maxerror,abs(actual-expected));assert abs(actual-expected)<1e-12
     if feature=='source_sink_L1':assert row['within_CID_rank_correlation'] is None
     checked+=1
  print('INDEPENDENT FRONTIER WORK MATRIX PASS',case,policy,flush=True)
 assert checked==72
 for p,h in r['bindings'].items():assert sha(p)==h
 summary={}
 for domain,target in itertools.product(plan['domains'],plan['targets']):
  dyn=[x for x in r['rows'] if x['domain']==domain and x['target']==target and x['feature']=='initial_min_same_layer_L1'];static={(x['case'],x['policy']):x for x in r['rows'] if x['domain']==domain and x['target']==target and x['feature']=='source_sink_L1'};entry={'initial_gap_higher_raw_spearman_pairs':sum(x['spearman'] is not None and static[x['case'],x['policy']]['spearman'] is not None and x['spearman']>static[x['case'],x['policy']]['spearman'] for x in dyn)}
  for name,values in [('initial_gap_spearman',[x['spearman'] for x in dyn]),('source_gap_spearman',[x['spearman'] for x in static.values()]),('initial_gap_within_CID',[x['within_CID_rank_correlation'] for x in dyn]),('initial_gap_within_seed_count',[x['within_exact_initial_unique_seed_count_rank_correlation'] for x in dyn])]:
   a=[v for v in values if v is not None];entry[name]=[min(a),max(a)] if a else None
  summary[domain+'__'+target]=entry
 bindings={str(p):sha(p) for p in [rp,Path(__file__),R/'tools/verify_CID_geometry_work_v1_2026_10_18.py',pp]}
 with (out/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all72_initial_frontier_static_gap_remaining_work_rank_statistics_verified',bindings=bindings,cells_verified=checked,max_formula_error=maxerror,summary=summary,scope=plan['scope']),f,indent=2)
 print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
