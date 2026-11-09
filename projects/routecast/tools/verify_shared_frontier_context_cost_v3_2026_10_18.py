"""Verify fixed comparison coverage, certified feature parity and cost accounting."""
import json,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';root=E/'mmc_shared_frontier_context_cost_v3_2026-10-18';rp=root/'results.json';r=json.loads(rp.read_text());pp=root/'protocol.json';plan=json.loads(pp.read_text());assert len(r['samples'])==4;oldroot=E/'mmc_source_frontier_restore_real_v2_2026-10-18';oldrp=oldroot/'verification.json';oldvp=oldroot/'independent_verification_v1.json';old=json.loads(oldrp.read_text());oldproof=json.loads(oldvp.read_text());assert sha(oldrp)==oldproof['bindings'][str(oldrp)];reference={}
 for row in old['rows']:
  assert sha(row['artifact'])==row['artifact_sha256'];reference[row['case']]=json.loads(Path(row['artifact']).read_text())[0]['pending_features']
 corep=E/'retained_tree_frontier_shared_core_v3_2026-10-18/verification.json';bp=E/'frontier_context_branches_v3_2026-10-18/verification.json';core=json.loads(corep.read_text());branch=json.loads(bp.read_text());assert core['commits']==320 and branch['branch_initial_edge_checks']==0;module=R/'tools/retained_tree_frontier_state_v3.py';assert sha(module)==core['bindings'][str(module)]==branch['bindings'][str(module)]==r['bindings'][str(module)];comparisons=0
 def near(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9),(a,b)
 for pair,order in enumerate(plan['order']):assert [x['arm'] for x in r['samples'] if x['pair']==pair]==order
 for sample in r['samples']:
  assert [x['case'] for x in sample['cases']]==plan['cases'] and sample['source_path_NET_admissions']==3 and sample['graph_geometry_admissions']==(1 if sample['arm']=='v3_shared_context' else 3)
  for case in sample['cases']:
   assert len(case['stages'])==3 and case['full_query_state_comparisons']==9*115572;comparisons+=case['full_query_state_comparisons'];assert all(case[k]>=0 for k in ['source_initialize_seconds','branch_seconds','reference_release_seconds','explicit_gc_seconds'])
   for stage in case['stages']:
    n=stage['stage'];receipt=stage['receipt'];assert receipt['generation']==n+1 and receipt['touched_NETs']==8 and stage['seconds']>=0
    if n==0:assert receipt['removed_connections']==14 and stage['features']==reference[case['case']]
    elif n==1:assert receipt['restored_connections']==14 and receipt['replaced_connections']==0 and not stage['features']
    else:assert receipt['replaced_connections']==14 and receipt['restored_connections']==0 and not stage['features']
  total=sample['shared_graph_context_initialize_seconds']+sample['shared_graph_context_release_seconds']+sum(c['source_initialize_seconds']+c['branch_seconds']+c['reference_release_seconds']+sum(s['seconds'] for s in c['stages']) for c in sample['cases']);near(total,sample['component_lifecycle_seconds_without_explicit_gc']);near(total+sample['explicit_gc_seconds'],sample['component_lifecycle_plus_explicit_gc_seconds']);assert sample['explicit_gc_seconds']>=sum(c['explicit_gc_seconds'] for c in sample['cases'])
 assert comparisons==12481776;pairs=[]
 for pair in range(2):
  values={x['arm']:x for x in r['samples'] if x['pair']==pair};a,b=values['v2_private_geometry'],values['v3_shared_context'];pairs.append(dict(pair=pair,old_component_seconds_without_explicit_gc=a['component_lifecycle_seconds_without_explicit_gc'],shared_component_seconds_without_explicit_gc=b['component_lifecycle_seconds_without_explicit_gc'],old_minus_shared_without_explicit_gc_seconds=a['component_lifecycle_seconds_without_explicit_gc']-b['component_lifecycle_seconds_without_explicit_gc'],old_component_plus_explicit_gc_seconds=a['component_lifecycle_plus_explicit_gc_seconds'],shared_component_plus_explicit_gc_seconds=b['component_lifecycle_plus_explicit_gc_seconds'],shared_graph_context_initialization_seconds=b['shared_graph_context_initialize_seconds']))
 for p,h in r['bindings'].items():assert sha(p)==h
 bindings={str(p):sha(p) for p in [rp,pp,Path(__file__),oldrp,oldvp,corep,bp]}
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='fixed_AB_BA_shared_context_lifecycles_feature_parity_and_cost_accounting_verified',bindings=bindings,complete_query_state_comparisons=comparisons,pairs=pairs,shared_lower_without_explicit_gc_in_both_pairs=all(x['old_minus_shared_without_explicit_gc_seconds']>0 for x in pairs),scope='Measured component lifecycle under fixed inputs only; both arms retain all initial path and NET checks. One graph admission reused across3source states; per-source path/NET initialization still charged3times. Explicit process-wide GC separate. Original quality/native/unseen/failure/complete-flow/hardware gates unchanged.'),f,indent=2)
 print(json.dumps(pairs,indent=2),flush=True)
if __name__=='__main__':main()
