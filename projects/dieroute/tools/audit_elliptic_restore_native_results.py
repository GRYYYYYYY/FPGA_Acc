"""Audit all frozen direct-restoration native outcomes, including invalid QoR."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_critical_net_restore_20261020'
def main():
 refs={}
 def sha(p):
  p=Path(p);h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  refs[str(p)]=h.hexdigest();return refs[str(p)]
 protocol=json.loads((D/'protocol.json').read_text());state=json.loads((D/'manifest.json').read_text());assert state['status']=='all_three_restore_probes_terminal_requires_independent_review'
 for p,h in protocol['source_sha256'].items():assert sha(p)==h,p
 pre=json.loads((D/'independent_preflight.json').read_text());results=[]
 for arm,done,check in zip(protocol['arms'],state['results'],pre['arms']):
  assert arm['name']==done['name']==check['name'];folder=D/arm['name'];tree=folder/'route.route_trees.csv';assert sha(tree)==done['tree_sha256']
  assert len(done['steps'])==2 and done['steps'][0]['returncode']==0
  p=folder/'native_validation/validation.json';q=json.loads(p.read_text());sha(p)
  native=folder/'native_validation'
  assert sha(native/'vpr_analysis.stdout')==q['stdout_sha256'];assert sha(native/'vpr_analysis.stderr')==q['stderr_sha256']
  assert sha(folder/'native.route')==q['inputs']['route_sha256']
  legal=q['legal'];assert legal==(q['vpr_exit_status']==0 and q['routing_consistency'] and q['vpr_succeeded'] and q['successfully_routed'])
  joint=legal and check['overused_resources']==0 and check['layer_transitions']<=pre['baseline']['layer_transitions'] and q['total_wirelength']<=q['baseline_wirelength'] and q['critical_path_delay_ns']<=q['baseline_cpd_ns']
  results.append({'name':arm['name'],'native_legal':legal,'native_exit_status':q['vpr_exit_status'],'overused_resources':check['overused_resources'],'reported_wirelength':q['total_wirelength'],'reported_cpd_ns':q['critical_path_delay_ns'],'reported_QoR_admissible':legal,'joint_quality_pass':joint})
 for p in [D/'protocol.json',D/'manifest.json',D/'independent_preflight.json',Path(__file__).resolve()]:sha(p)
 result={'status':'three_direct_restore_native_results_independently_reviewed','arms':results,'source_sha256':refs,'scope':'Invalid routing may still print lower delay or wirelength. Such QoR is not admissible benefit. Posterior probes preserve all failures and do not replace original12cohort. No adoption.','research_complete':False,'adopted':False}
 with (D/'independent_native_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(results))
if __name__=='__main__':main()
