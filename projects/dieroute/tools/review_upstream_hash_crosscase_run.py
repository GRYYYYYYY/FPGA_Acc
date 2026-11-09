"""Run native legality review for one successfully terminal cross-case attempt."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'work/upstream_hash_crosscase_pairs_20261018'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('label');p.add_argument('--check-only',action='store_true');a=p.parse_args()
 protocol=json.loads((D/'protocol.json').read_text());entry,=[v for v in protocol['steps'] if v['label']==a.label]
 for f,h in protocol['source_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
 m=json.loads((D/'manifest.json').read_text());matches=[v for v in m['steps'] if v['label']==a.label];ready=len(matches)==1 and matches[0].get('returncode')==0
 if a.check_only:print(json.dumps({'label':a.label,'ready':ready,'launched':False}));return
 assert ready,'Crosscase run not successfully terminal'
 run=D/'runs'/a.label;recipe=D/'recipes'/entry['case']/entry['arm']/'pair.json';cfg=json.loads(recipe.read_text())['steps'][0];envcfg=cfg['routing_environment']
 cp=R/'work/native_refreshed_critical_policy_v1_20261016/protocol.json';case,=[v for v in json.loads(cp.read_text())['cases'] if v['label']==entry['case']];assert cfg['command'][1]==case['input_prefix']
 tools=R/'work/rr_remaining_layer_tail_variant_20261015/native_tools';vpr=R/'work/vpr_four_layer_build_20261015/build/vpr/vpr';native=Path(case['native_case'])
 commands=[('tree',['/usr/bin/python3',str(tools/'audit_rr_final_tree_state.py'),case['input_prefix'],str(run/'route'),'--report',str(run/'tree_audit.json')]),('provenance',['/usr/bin/python3',str(tools/'audit_persistent_session_provenance.py'),str(recipe),str(run)]),('writeback',['/usr/bin/python3',str(R/'work/rr_fanout_present_interaction_variant_v2_20261015/source/persistroute/tools/write_vpr_route.py'),str(native/'circuit.route'),str(native/'rr_graph.xml'),case['connections'],str(run/'route.route_trees.csv'),str(run/'native.route')])]
 cmd=['/usr/bin/python3',str(tools/'validate_vpr_route_device.py'),'--vpr',str(vpr),'--device',envcfg['PERSISTROUTE_VPR_DEVICE']]
 for flag,name in [('arch','architecture.xml'),('circuit','circuit.blif'),('net','circuit.net'),('place','circuit.place'),('rr-graph','rr_graph.xml')]:cmd+=['--'+flag,str(native/name)]
 cmd+=['--route',str(run/'native.route'),'--channel-width',envcfg['PERSISTROUTE_VPR_CHAN_WIDTH'],'--work-dir',str(run/'native_validation'),'--baseline-wirelength',str(case['baseline_wirelength']),'--baseline-cpd-ns',str(case['baseline_cpd_ns'])];commands.append(('native',cmd))
 out=D/'native_reviews'/a.label;out.mkdir(parents=True,exist_ok=False);files=[Path(__file__).resolve(),cp,D/'protocol.json']+[Path(cmd[1]) for _,cmd in commands];(out/'protocol.json').write_text(json.dumps({'commands':commands,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}},indent=2)+'\n')
 m={'status':'running','pid':os.getpid(),'steps':[],'research_complete':False};env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE','PERSISTROUTE'))}
 for name,cmd in commands:
  with (out/(name+'.log')).open('x') as f:
   start=time.monotonic_ns();s=subprocess.run(cmd,cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
  m['steps'].append({'label':name,'returncode':s.returncode,'wall_ns':time.monotonic_ns()-start});(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');assert s.returncode==0,name
 m['status']='native_review_commands_terminal_requires_interpretation';(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(m['status'])
if __name__=='__main__':main()
