"""Require native legality and all baseline quality gates for capacity closure."""
from pathlib import Path
import csv,hashlib,json
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_capacity_restore_closure_20261020'
def main():
 refs={}
 def sha(p):
  p=Path(p);h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  refs[str(p)]=h.hexdigest();return refs[str(p)]
 p=json.loads((D/'protocol.json').read_text());s=json.loads((D/'manifest.json').read_text());assert s['status']=='all_three_restore_probes_terminal_requires_independent_review'
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 construction=json.loads((D/'construction.json').read_text());pre=json.loads((D/'independent_preflight.json').read_text())
 for e in [construction,pre]:
  for f,h in e['source_sha256'].items():assert sha(f)==h,f
 assert len(s['results'])==1;arm=s['results'][0];folder=D/arm['name'];tree=folder/'route.route_trees.csv'
 assert sha(tree)==arm['tree_sha256']
 constructed=Path(construction['arms'][0]['tree']);assert sha(constructed)==construction['arms'][0]['tree_sha256']
 def canonical(path):
  with path.open() as f:return sorted(tuple(int(row[k]) for k in ['net_id','source','parent','child']) for row in csv.DictReader(f))
 assert canonical(tree)==canonical(constructed),'Actual evaluated net tree differs from independently constructed mixture'
 assert arm['steps'][0]['returncode']==0 and len(arm['steps'])==2
 qfile=folder/'native_validation/validation.json';q=json.loads(qfile.read_text());sha(qfile)
 assert sha(folder/'native.route')==q['inputs']['route_sha256']
 assert sha(folder/'native_validation/vpr_analysis.stdout')==q['stdout_sha256']
 assert sha(folder/'native_validation/vpr_analysis.stderr')==q['stderr_sha256']
 check=pre['arms'][0];assert check['overused_resources']==0 and check['all_tree_nodes_and_sinks_reachable']
 checks={'native_legal':q['legal'],'native_process_success':q['vpr_exit_status']==0,'native_consistency':q['routing_consistency'],'capacity':check['overused_resources']==0,'wirelength':q['total_wirelength']<=q['baseline_wirelength'],'CPD':q['critical_path_delay_ns']<=q['baseline_cpd_ns'],'modeled_transitions':check['layer_transitions']<=pre['baseline']['layer_transitions']}
 for f in [D/'protocol.json',D/'manifest.json',D/'construction.json',D/'independent_preflight.json',Path(__file__).resolve()]:sha(f)
 result={'status':'posterior_capacity_closure_native_joint_pass' if all(checks.values()) else 'posterior_capacity_closure_native_joint_fail','checks':checks,'restored_nets':2220,'retained_candidate_nets':464,'wirelength':q['total_wirelength'],'baseline_wirelength':q['baseline_wirelength'],'cpd_ns':q['critical_path_delay_ns'],'baseline_cpd_ns':q['baseline_cpd_ns'],'modeled_layer_transitions':check['layer_transitions'],'baseline_modeled_layer_transitions':pre['baseline']['layer_transitions'],'validation_wall_ns':arm['wall_ns'],'source_sha256':refs,'scope':'One posterior repair probe, exact whole-net mixture and independent capacity/native provenance checks. Charge all failed direct probes and restoration validation costs separately. Does not replace original12case cohort or establish generalized algorithm, hardware acceleration or physical SLL benefit. No adoption.','adopted':False,'research_complete':False}
 with (D/'independent_native_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
