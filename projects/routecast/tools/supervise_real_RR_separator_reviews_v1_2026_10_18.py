"""Review every frozen input-only profile; preserve UNKNOWN and all cases."""
import json,sys,time,subprocess,os,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
root=R/'experiments/width_stress_RR_separator_profiles_v2_2026-10-18'
def alive(p):
 try:s=Path('/proc',str(p['pid']),'stat').read_text().split(') ',1)[1].split()
 except FileNotFoundError:return False
 return s[19]==p['startticks'] and s[0]!='Z'
def save(status,**kw):(root/'review_supervision.json').write_text(json.dumps(dict(status=status,**kw),indent=2)+'\n')
def main():
 producer=json.loads((root/'live_process.json').read_text());spec=R/'experiments/width_stress_RR_separator_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());logs=root/'review_logs';logs.mkdir();s=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(root/'review_live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=s[19]))+'\n');rows=[];bindings={str(spec):sha(spec),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
 for name in p['cases']:
  folder=root/name;profile=folder/'profiles.json';save('waiting_exact_input_profile_producer',case=name,producer=producer,completed=len(rows))
  while True:
   if profile.exists():
    try:d=json.loads(profile.read_text());assert d['status']=='real_RR_separator_profiles_complete_independent_literal_review_pending';break
    except json.JSONDecodeError:
     if not alive(producer):raise
   if not alive(producer):raise RuntimeError('Required profile missing after exact producer terminal; no routed fallback or regeneration')
   time.sleep(3)
  proof=folder/'independent_literal_verification_v1.json';save('independent_literal_RR_separator_review_running',case=name,completed=len(rows))
  if not proof.exists():
   with (logs/f'{name}.log').open('x') as log:code=subprocess.call([sys.executable,str(R/'tools/verify_real_RR_separator_profiles_v1_2026_10_18.py'),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   assert code==0,(name,code)
  v=json.loads(proof.read_text());assert v['status']=='independent_all_real_RR_plane_memberships_demands_capacities_and_endpoint_identity_pass' and all(sha(k)==h for k,h in v['bindings'].items());bindings[str(proof)]=sha(proof);rows.append(dict(name=name,proof=str(proof),capacity_bound_result=v['capacity_bound_result'],integer_planes_verified=v['integer_planes_verified'],physical_NETs=v['physical_NETs'],physical_queries=v['physical_queries']));print('INDEPENDENT_REAL_SEPARATOR_PROFILE',name,v['capacity_bound_result'],flush=True)
 (root/'independent_cohort_verification_v1.json').write_text(json.dumps(dict(status='all4_input_only_separator_profiles_independently_verified',bindings=bindings,cases=rows,any_positive_capacity_bound=any(x['capacity_bound_result']=='CONDITIONAL_CAPACITY_INFEASIBILITY_CERTIFICATE' for x in rows),scope='All4 frozen input profiles, conditional on authenticated same-input ignored NET scope; native outcomes not used. UNKNOWN never becomes routable. No native-policy classification, heldout, route quality, hardware or gain claim.'),indent=2)+'\n');save('all4_literal_RR_profile_reviews_complete',cases=len(rows))
if __name__=='__main__':
 try:main()
 except Exception:save('independent_profile_review_failed',error=traceback.format_exc());raise
