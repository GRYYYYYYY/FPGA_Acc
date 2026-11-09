"""Fixed72cell measured-frontier versus static endpoint-gap diagnostic."""
import array,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from evaluate_CID_geometry_work_v1_2026_10_18 import doubled,corr
MAX=2**64-1

def main():
 E=R/'experiments';src=E/'mmc_initial_frontier_replay_v1_2026-10-18';rp=src/'verification.json';vp=src/'independent_verification_v1.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert sha(rp)==v['bindings'][str(rp)] and len(v['rows'])==6;pp=E/'mmc_native_connection_seed_phase_v1_2026-10-18/frontier_geometry_analysis_protocol_v1.json';plan=json.loads(pp.read_text());out=E/'mmc_initial_frontier_work_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [rp,vp,pp,Path(__file__),R/'tools/evaluate_CID_geometry_work_v1_2026_10_18.py',R/'tools/diagnose_NET_length_confounding_v1_2026_10_18.py']};rows=[];coverage=[]
 for row in r['rows']:
  case,policy=row['case'],row['arm'];desc=row['frontier_file'];assert sha(desc['path'])==desc['sha256'];bindings[desc['path']]=desc['sha256'];columns={k:array.array('Q') for k in ['CID','mode','unique','minimum','source','remaining','pops']}
  with open(desc['path'],'rb') as f:
   assert f.readline()==b'RC_INITIAL_FRONTIER_LE64 1\n';seq=0
   while block:=f.read(96*(1<<14)):
    assert len(block)%96==0
    for z in struct.iter_unpack('<12Q',block):
     seq+=1;assert z[0]==seq and z[7]>=z[3];values=[z[1],z[2],z[4],z[5],z[6],z[7]-z[3],z[8]]
     for a,n in zip(columns.values(),values):a.append(n)
  assert seq==row['attempts'];coverage.append(dict(case=case,policy=policy,attempts=seq,undefined_initial_gap=sum(x==MAX for x in columns['minimum'])))
  for domain in plan['domains']:
   mode=None if domain.startswith('all_') else 0 if domain.startswith('normal_') else 1;ids=[i for i in range(seq) if columns['minimum'][i]!=MAX and (mode is None or columns['mode'][i]==mode)];cid=[columns['CID'][i] for i in ids];unique=[columns['unique'][i] for i in ids];scores={'initial_min_same_layer_L1':[columns['minimum'][i] for i in ids],'source_sink_L1':[columns['source'][i] for i in ids]};targets={'remaining_heap_pushes_after_initial_seed_inserts':[columns['remaining'][i] for i in ids],'total_heap_pops':[columns['pops'][i] for i in ids]};ranked={k:doubled(y) for k,y in targets.items()}
   for feature,x in scores.items():
    xr=doubled(x)
    for target,yr in ranked.items():
     within=corr(xr,yr,cid);assert feature!='source_sink_L1' or within is None;rows.append(dict(case=case,policy=policy,domain=domain,feature=feature,target=target,attempts=len(ids),spearman=corr(xr,yr),within_CID_rank_correlation=within,within_exact_initial_unique_seed_count_rank_correlation=corr(xr,yr,unique)))
  print('INITIAL FRONTIER WORK MATRIX CASE',case,policy,flush=True)
 assert len(rows)==72 and all(sha(p)==h for p,h in bindings.items())
 with (out/'results.json').open('x') as f:json.dump(dict(status='all72_fixed_frontier_static_gap_work_diagnostics_computed',bindings=bindings,coverage=coverage,rows=rows,scope=plan['scope'],independent_verification_pending=True),f,indent=2)
if __name__=='__main__':main()
