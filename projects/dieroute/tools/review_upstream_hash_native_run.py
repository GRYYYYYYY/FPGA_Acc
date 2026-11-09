"""Native review of one successfully terminal run in the frozen hash-set study."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'work/upstream_target_hash_native_pairs_20261018'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('label');p.add_argument('--check-only',action='store_true');a=p.parse_args()
 protocol=json.loads((D/'protocol.json').read_text());allowed={s['label'] for s in protocol['steps']};assert a.label in allowed
 for f,h in protocol['source_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
 state=json.loads((D/'manifest.json').read_text());matches=[s for s in state['steps'] if s['label']==a.label];ready=len(matches)==1 and matches[0].get('returncode')==0
 if a.check_only:print(json.dumps({'ready':ready,'launched':False}));return
 assert ready,'Run not successfully terminal'
 run=D/'runs'/a.label;arm=a.label.split('_')[1];recipe=D/'recipes'/arm/'pair.json'
 cfg=json.loads(recipe.read_text())['steps'][0];case=R/'work/native_sb_layer_capacity_scaling_20261015/layers3_cw80';pre=R/'work/sb_native_roundtrip_preflight_20261015/layers3_cw80';tools=R/'work/rr_remaining_layer_tail_variant_20261015/native_tools';vpr=R/'work/vpr_four_layer_build_20261015/build/vpr/vpr'
 commands=[('tree',['/usr/bin/python3',str(tools/'audit_rr_final_tree_state.py'),cfg['command'][1],str(run/'route'),'--report',str(run/'tree_audit.json')]),('provenance',['/usr/bin/python3',str(tools/'audit_persistent_session_provenance.py'),str(recipe),str(run)]),('writeback',['/usr/bin/python3',str(R/'work/rr_fanout_present_interaction_variant_v2_20261015/source/persistroute/tools/write_vpr_route.py'),str(case/'circuit.route'),str(case/'rr_graph.xml'),str(pre/'connections.csv'),str(run/'route.route_trees.csv'),str(run/'native.route')])]
 cmd=['/usr/bin/python3',str(tools/'validate_vpr_route_device.py'),'--vpr',str(vpr),'--device','DieRouteSBScale3']
 for flag,name in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:cmd+=['--'+flag,str(case/name)]
 cmd+=['--route',str(run/'native.route'),'--channel-width','80','--work-dir',str(run/'native_validation'),'--baseline-wirelength','11615','--baseline-cpd-ns','10.4531'];commands.append(('native',cmd))
 out=D/'native_reviews'/a.label;out.mkdir(parents=True,exist_ok=False)
 hashes={str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 for name,cmd in commands:
  f=Path(cmd[1]);hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 (out/'protocol.json').write_text(json.dumps({'commands':commands,'source_sha256':hashes,'scope':'Native legality/QoR commands; interpretation and input hashes require review.'},indent=2)+'\n')
 m={'status':'running','pid':os.getpid(),'steps':[],'research_complete':False};env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE','PERSISTROUTE'))}
 for name,cmd in commands:
  with (out/(name+'.log')).open('x') as log:
   start=time.monotonic_ns();result=subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
  m['steps'].append({'label':name,'returncode':result.returncode,'wall_ns':time.monotonic_ns()-start});(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert result.returncode==0,name
 m['status']='native_commands_terminal_requires_independent_interpretation';(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(m['status'])
if __name__=='__main__':main()
