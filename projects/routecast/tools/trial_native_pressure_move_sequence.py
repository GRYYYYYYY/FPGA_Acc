"""Frozen consecutive-move payloads: native legality and QoR, no timing gain claim."""
import collections,json,os,re,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha,placements
from stream_native_route_audit import audit


def main():
 base=Path('experiments');sequence=base/'adder_tree_2L032_move_sequence_2026-10-06';predictions=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 out=base/'native_pressure_move_sequence_trial_2026-10-06';work=Path('work/native_pressure_move_sequence_trial_2026-10-06');out.mkdir();work.mkdir();(out/'source').mkdir();bindings={}
 def load(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
 sr=load(sequence/'receipt.json');sp=load(sequence/'protocol.json');assert sr['protocol_sha256']==sha(sequence/'protocol.json');pr=load(predictions/'receipt.json');inputs=sp['inputs']
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values()) and all(sha(p)==h for p,h in pr['inputs_sha256'].items())
 build=Path('build/native_pressure_feedback_v2_2026-10-06');br=load(build/'receipt.json');binary=build/'routecast_pressure_vpr';assert sha(binary)==br['binary_sha256'];bindings[str(binary)]=sha(binary)
 for name in ('trial_native_pressure_move_sequence.py','pre_route_endpoints.py','stream_native_route_audit.py','audit_native_route.py'):
  source=Path('tools')/name;shutil.copyfile(source,out/'source'/name);bindings[str(source)]=sha(source)
 protocol={'inputs':inputs,'bindings_sha256':bindings,'sequence_receipt_sha256':sha(sequence/'receipt.json'),'prediction_receipt_sha256':sha(predictions/'receipt.json'),'seed':1,'channel_width':300,'workers':1,'scope':'Preselected three consecutive placements, precomputed incremental pressure; each off/on native cold route from fixed placement, not persistent native route reuse. One sample per mode per step; native-only wall, no total-time gain or unseen-family claim.'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
 for step in sr['steps']:
  i=step['step'];assert all(sha(sequence/name)==digest for name,digest in step['outputs_sha256'].items());ep=load(sequence/f'step_{i}_endpoints.json');place=sequence/f'step_{i}.place'
  proof=next(v for v in pr['steps'] if v['step']==i);payload=predictions/f'step_{i}.pressure';assert sha(payload)==proof['pressure_sha256'];bindings[str(payload)]=sha(payload);nodes=len(payload.read_text().splitlines())-1
  for mode in ('off','on'):
   tag=f'{i:02d}_{mode}';wd=work/tag;wd.mkdir()
   for key,name in [('atom','design.blif'),('packed_netlist','design.net')]:shutil.copyfile(inputs[key]['path'],wd/name)
   shutil.copyfile(place,wd/'design.place');env=dict(os.environ)
   for key in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(key,None)
   if mode=='on':env['ROUTECAST_PRESSURE_FILE']=str(payload.resolve());env['ROUTECAST_EXPECT_GRAPH_SHA256']=inputs['rr_graph']['sha256']
   command=[str(binary.resolve()),inputs['architecture']['path'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',inputs['rr_graph']['path'],'--route_chan_width','300','--num_workers','1','--seed','1','--max_router_iterations','100']
   (out/(tag+'_command.json')).write_text(json.dumps({'command':command,'cwd':str(wd.resolve())})+'\n');start=time.monotonic()
   with (out/(tag+'.log')).open('w') as log:code=subprocess.run(command,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
   wall=time.monotonic()-start;assert code==0;text=(out/(tag+'.log')).read_text()
   assert all(marker in text for marker in ('VPR succeeded','Completed placement consistency check successfully','Completed routing consistency check successfully'))
   if mode=='on':assert f'RouteCast pressure applied: {nodes} channel nodes' in text
   else:assert 'RouteCast pressure applied' not in text
   assert placements(wd/'design.place',inputs['packed_netlist']['sha256'])==placements(place,inputs['packed_netlist']['sha256'])
   physical=audit(inputs['rr_graph']['path'],wd/'design.route');identity=lambda rows:collections.Counter((r['net_id'],r['source'],r['sink']) for r in rows)
   assert identity(physical['connections'])==identity(ep['connections']) and physical['all_printed_branch_arc_switch_and_union_checks_pass'] and physical['overflow_units']==0
   path=out/(tag+'_physical.json');path.write_text(json.dumps(physical)+'\n')
   row={'step':i,'mode':mode,'native_wall_s':wall,'connections':len(physical['connections']),'pressure_nodes':nodes if mode=='on' else 0,'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1]),'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),'route_sha256':sha(wd/'design.route'),'log_sha256':sha(out/(tag+'.log')),'physical_sha256':sha(path)};results.append(row);print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items()) and all(sha(v['path'])==v['sha256'] for v in inputs.values())
 (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'final_bindings_sha256':bindings,'results':results,'all_physical_and_placement_checks_pass':True,'scope':protocol['scope']},indent=2)+'\n')

if __name__=='__main__':main()
