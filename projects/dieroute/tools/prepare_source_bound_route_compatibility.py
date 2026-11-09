"""Prepare observed-route compatibility checks using an already source-audited VPR."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'work/source_bound_route_compatibility_20261020'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 D.mkdir();build=R/'work/vpr_source_bound_timing_build_20261015';bound=json.loads((build/'build_dependency_audit.json').read_text());binary=Path(bound['binary']);assert sha(binary)==bound['binary_sha256'];groups=[]
 specs=[('elliptic',R/'work/elliptic_native_RC_observation_20261020',R/'work/elliptic_local_exchange_20261020/native_queue/task2926_forward/candidate'),('apex2',R/'work/apex2_seed1_exchange_native_observation_20261020',R/'work/apex2_seed1_stage3_current_ceiling_20261020/native_queue/task1289_forward/candidate')]
 for label,old,route_directory in specs:
  G=D/label;G.mkdir();template=json.loads((old/'protocol.json').read_text());baseline=next(v for v in template['cases'] if v['name']=='baseline');cases=[];expected={};files={build/'build_dependency_audit.json',build/'result.json',old/'protocol.json',old/'independent_audit.json',old/'baseline/native_observations.csv',old/'baseline/native_validation/validation.json',route_directory/'native.route',route_directory/'native_validation/validation.json',R/'tools/run_native_RC_observations.py',Path(__file__).resolve()}
  for name,route,executable in [('baseline_source_bound',Path(baseline['command'][baseline['command'].index('--route')+1]),binary),('candidate_legacy',route_directory/'native.route',None),('candidate_source_bound',route_directory/'native.route',binary)]:
   c=json.loads(json.dumps(baseline));c['name']=name;command=c['command'];command[command.index('--route')+1]=str(route);command[command.index('--work-dir')+1]=str(G/name/'native_validation')
   if executable:command[command.index('--vpr')+1]=str(executable)
   c['environment']['PERSISTROUTE_VPR_TIMING_OUTPUT']=str(G/name/'native_observations.csv');(G/name).mkdir();cases.append(c);files.update(Path(v) for v in command if Path(v).is_file());files.add(Path(c['environment']['PERSISTROUTE_VPR_TIMING_INPUT']))
  comparisons=[{'name':'baseline','legacy_csv':str(old/'baseline/native_observations.csv'),'legacy_validation':str(old/'baseline/native_validation/validation.json'),'source_bound_case':'baseline_source_bound'},{'name':'candidate','legacy_csv':str(G/'candidate_legacy/native_observations.csv'),'legacy_validation':str(G/'candidate_legacy/native_validation/validation.json'),'source_bound_case':'candidate_source_bound'}]
  p={'status':'frozen_before_launch','cases':cases,'connections':template['connections'],'comparisons':comparisons,'expected_candidate_validation':str(route_directory/'native_validation/validation.json'),'source_sha256':{str(f):sha(f) for f in files},'scope':'Twofrozenroutesinonecase;native+routed0queriescomparelegacytoalready-source-boundtool. Doesnotreplaceoriginalbinaryorfrozenexperiments,provehistoricalas-builtidentityorall-inputequivalence. No speedclaim.'};(G/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');groups.append({'label':label,'directory':str(G)})
 (D/'protocol.json').write_text(json.dumps({'groups':groups,'source_bound_build_audit':str(build/'build_dependency_audit.json'),'source_sha256':{str(D/g['label']/'protocol.json'):sha(D/g['label']/'protocol.json') for g in groups},'scope':'Cross-caseobservedcompatibilityextension,notuniversalproof.'},indent=2)+'\n');print(json.dumps(groups))
if __name__=='__main__':main()
