"""Recheck twelfth posterior route's native inputs and modeled layer transitions."""
from pathlib import Path
import array,hashlib,json,sys
from audit_width_parent_crossings import tree_count
R=Path(__file__).resolve().parents[1]
def main():
 label='elliptic_28x22_cw320_seed1';p=R/'work/width_coverage_parents_20261018/parents'/label
 b=R/'work/width_coverage_roundtrip_20261017'/label
 native=p/'native_validation';review=R/f'work/width_parent_review_{label}_20261018'
 refs={}
 def sha(f):
  f=Path(f);h=hashlib.sha256(f.read_bytes()).hexdigest();refs[str(f.resolve())]=h;return h
 m=json.loads((review/'manifest.json').read_text());assert m['status']=='review_commands_terminal_requires_evidence_interpretation' and len(m['steps'])==4 and all(v['returncode']==0 for v in m['steps'])
 a=json.loads((native/'validation.json').read_text());assert all(a[k] for k in ['legal','route_loaded','routing_consistency','successfully_routed','vpr_succeeded']) and a['vpr_exit_status']==0
 cmd=a['command'];files={'vpr':Path(cmd[0]),'arch':Path(cmd[1]),'circuit':Path(cmd[2]),'net':native/'circuit.net','place':native/'circuit.place','route':native/'native.route','rr_graph':Path(cmd[cmd.index('--read_rr_graph')+1])}
 for k,f in files.items():assert sha(f)==a['inputs'][k+'_sha256'],k
 assert sha(native/'vpr_analysis.stdout')==a['stdout_sha256']
 assert sha(native/'vpr_analysis.stderr')==a['stderr_sha256']
 baseline=json.loads((b/'audit.json').read_text())
 for f,h in baseline['source_sha256'].items():assert sha(f)==h,f
 dies=array.array('H');dies.frombytes((b/'topology.node_die').read_bytes())
 if sys.byteorder!='little':dies.byteswap()
 assert len(dies)==baseline['nodes'] and set(dies)=={0,1,2}
 before,nb=tree_count(b/'native_tree.csv',dies);after,na=tree_count(p/'route.route_trees.csv',dies);assert nb==baseline['tree_edges']
 for f in [b/'topology.node_die',b/'native_tree.csv',p/'route.route_trees.csv',p/'tree_audit.json',p/'session_provenance_audit.json',p/'manifest.json',native/'validation.json',review/'manifest.json',review/'protocol.json',Path(__file__),R/'tools/audit_width_parent_crossings.py']:sha(f)
 for name in ['tree_audit.json','session_provenance_audit.json']:
  z=json.loads((p/name).read_text())
  for f,h in z.get('source_sha256',{}).items():assert sha(f)==h,f
 result={'status':'twelfth_posterior_parent_native_inputs_outputs_and_crossings_reviewed','label':label,'native_legal':True,'wirelength':a['total_wirelength'],'cpd_ns':a['critical_path_delay_ns'],'wirelength_delta_percent':a['wirelength_delta_percent'],'cpd_delta_percent':a['cpd_delta_percent'],'baseline_layer_transitions':before,'candidate_layer_transitions':after,'baseline_tree_edges':nb,'candidate_tree_edges':na,'joint_observed_nonincrease':after<=before and a['wirelength_delta_percent']<=0 and a['cpd_delta_percent']<=0,'source_sha256':refs,'scope':'Twelfth of12 posterior configurations, three circuits seed1; modeled net-deduplicated layer transitions, not physical SLL. Not heldout replacement, generalization or board performance.','research_complete':False}
 out=R/'work/width_coverage_twelfth_parent_evidence_20261018';out.mkdir()
 (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
