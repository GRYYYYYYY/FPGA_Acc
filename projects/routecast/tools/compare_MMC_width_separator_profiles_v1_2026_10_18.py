"""Paired verified profiles: preserve UNKNOWN, never infer routing success."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expanded(p,proof):
 answer={}
 for axis in ['x','y']:
  rows=p['profiles'][axis]['cuts'];start=rows[0]['cut_after_coordinate'];count=proof['profiles'][axis]['integer_planes_verified'];i=0
  for k in range(start,start+count):
   while i+1<len(rows) and rows[i+1]['cut_after_coordinate']<=k:i+=1
   row=rows[i];answer[axis,k]=(row['mandatory_unique_NETs'],row['separator_capacity'])
 return answer

def main():
 root=R/'experiments/width_stress_RR_separator_profiles_v2_2026-10-18';bindings={str(Path(__file__).resolve()):sha(Path(__file__).resolve())};profiles={};summaries={}
 for name in ['mmc_width64','mmc_width96']:
  pp=root/name/'profiles.json';vp=root/name/'independent_literal_verification_v1.json';p=json.loads(pp.read_text());v=json.loads(vp.read_text());assert v['status']=='independent_all_real_RR_plane_memberships_demands_capacities_and_endpoint_identity_pass';assert v['bindings'][str(pp)]==sha(pp);assert v['capacity_bound_result']=='UNKNOWN_NO_POSITIVE_CAPACITY_BOUND';profiles[name]=expanded(p,v)
  for q in [pp,vp]:bindings[str(q)]=sha(q)
  summaries[name]={}
  for axis in ['x','y']:
   rows=[(k,d,c) for (a,k),(d,c) in profiles[name].items() if a==axis];k,d,c=max(rows,key=lambda x:x[1]/x[2] if x[2] else -1);summaries[name][axis]=dict(max_load_observation_cut=k,mandatory_NETs=d,separator_capacity=c,ratio_numerator=d,ratio_denominator=c)
 a,b=profiles['mmc_width64'],profiles['mmc_width96'];assert a.keys()==b.keys();same=sum(a[k][0]==b[k][0] for k in a);increases=sum(b[k][1]>a[k][1] for k in a);decreases=[list(k) for k in a if b[k][1]<a[k][1]];failure=R/'experiments/prospective_native_width_stress_v1_2026-10-18/mmc_width64/independent_outcome_verification_v1.json';f=json.loads(failure.read_text());assert f['outcome']=='OBSERVED_NATIVE_ROUTING_FAILURE_UNDER_FIXED100ITER_BUDGET';bindings[str(failure)]=sha(failure)
 result=dict(status='two_verified_MMC_width_profiles_reconciled_partial_four_case_study',bindings=bindings,integer_planes_per_configuration=len(a),same_mandatory_demand_planes=same,wider_graph_increased_separator_capacity_planes=increases,wider_graph_decreased_separator_capacity_planes=decreases,descriptive_max_load_observations=summaries,both_capacity_bound_results='UNKNOWN_NO_POSITIVE_CAPACITY_BOUND',known_width64_native_failure_reason=f['reason'],interpretation='The valid necessary bound does not certify the observed width64 native wirelength-policy failure. Both UNKNOWN outcomes must remain UNKNOWN; neither graph feasibility nor model classification accuracy follows. Max ratios are descriptions over all retained planes, not selected feature thresholds.',four_case_study_complete=False,next_action='Keep the registered four-case queue; await both XTEA graphs and independently verify all profiles. Do not optimize or claim failure prediction from this two-case partial result.',scope='Descriptive reconciliation after input-only profiles; native outcome is used here for interpretation only, never as a profile-generation input. Both families remain exposed.')
 (root/'MMC_partial_profile_reconciliation_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print('PAIRED_REAL_PROFILES_RECONCILED',len(a),same,increases,len(decreases),summaries)
if __name__=='__main__':main()
