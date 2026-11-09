"""Independently review actual three-layer matched pilot outcomes and provenance."""
import csv,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'work/sb_three_layer_matched_pilot_20261015'
cache={}
def sha(q):
 q=Path(q).resolve()
 if str(q) not in cache:
  h=hashlib.sha256()
  with q.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[str(q)]=h.hexdigest()
 return cache[str(q)]
def load(q):return json.loads(Path(q).read_text())
def refs(x):
 for q,h in x.get('source_sha256',{}).items():assert sha(q)==h,q
def main():
 protocol=load(P/'protocol.json');launch=load(P/'launch_protocol.json');refs(protocol);refs(launch)
 manifest=load(P/'manifest.json');result=load(P/'result.json')
 assert manifest['status']==result['status']=='two_arm_three_layer_pilot_complete'
 assert protocol['modes']==['flat','downstream_bounded'] and protocol['repeats']==1
 assert all(s['status']=='passed' and s['returncode']==0 for s in manifest['steps']) and len(manifest['steps'])==10
 case=Path(protocol['case']);pre=Path(protocol['topology_prefix']).parent
 owners=[r[0] for r in struct.iter_unpack('<H',Path(protocol['topology_prefix']+'.node_die').read_bytes())]
 def crossings(q):
  edges=set()
  for r in csv.DictReader(Path(q).open()):
   n,a,b=(int(r[k]) for k in ('net_id','parent','child'))
   assert 0<=a<len(owners) and 0<=b<len(owners)
   if owners[a]!=owners[b]:edges.add((n,a,b))
  return len(edges)
 baseline=crossings(pre/'native_tree.csv');assert baseline==999
 rows=[];environments=[];commands=[]
 for mode in protocol['modes']:
  d=P/'native_runs'/(mode+'_0');recipe=load(P/'recipes'/mode/'pair.json');step=recipe['steps'][0]
  environment=step['routing_environment'];environments.append(environment);commands.append(step['command'])
  run=load(d/'manifest.json');refs(run);assert run['returncode']==0 and run['command'][-1]==mode
  replay=load(d/'replay_audit.json');refs(replay);assert replay['cpu_legal'] and replay['final_resources_and_costs_byte_equivalent']
  tree=load(d/'tree_audit.json');refs(tree);assert tree['status']=='final_native_rr_tree_connectivity_and_resource_memberships_reconstructed'
  timing=load(d/'session_provenance_audit.json');refs(timing);assert timing['status']=='actual_persistent_session_inputs_binary_tasks_and_request_lineage_audited'
  route=load(d/'route.json');assert route['legal'] and route['mode']==mode and route['iterations']==replay['epochs']==timing['epochs']
  q=load(d/'native_validation/validation.json');assert q['legal'] and q['vpr_exit_status']==0
  stdout=d/'native_validation/vpr_analysis.stdout';stderr=d/'native_validation/vpr_analysis.stderr'
  assert sha(stdout)==q['stdout_sha256'] and sha(stderr)==q['stderr_sha256'];text=stdout.read_text()
  for marker in ['Finished loading route file','Completed routing consistency check successfully.','Circuit successfully routed','VPR succeeded']:assert marker in text
  assert int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1])==q['total_wirelength']
  assert float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1])==q['critical_path_delay_ns']
  assert q['command'][q['command'].index('--device')+1]=='DieRouteSBScale3'
  for k,path in [('vpr',Path(q['command'][0])),('arch',case/'architecture.xml'),('circuit',case/'circuit.blif'),('net',case/'circuit.net'),('place',case/'circuit.place'),('route',d/'native.route'),('rr_graph',case/'rr_graph.xml')]:assert sha(path)==q['inputs'][k+'_sha256']
  count=crossings(d/'route.route_trees.csv');r=result['outcomes'][mode];assert r['native_qor']==q and r['model_crossings']==count and r['baseline_model_crossings']==baseline
  checks=dict(native_legal=True,wirelength_nondegrade=q['total_wirelength']<=11615,cpd_nondegrade=q['critical_path_delay_ns']<=10.4531,model_crossings_nondegrade=count<=baseline)
  assert r['checks']==checks
  rows.append(dict(mode=mode,iterations=route['iterations'],native_wirelength=q['total_wirelength'],native_cpd_ns=q['critical_path_delay_ns'],model_crossings=count,checks=checks,joint_gate_pass=all(checks.values())))
  for f in [d/'route.json',d/'native.route',d/'native_validation/validation.json',d/'replay_audit.json',d/'tree_audit.json',d/'session_provenance_audit.json']:sha(f)
 assert environments[0]==environments[1]
 assert commands[0][:-1]==commands[1][:-1]
 assert environments[0]['PERSISTROUTE_VPR_DEVICE']=='DieRouteSBScale3' and environments[0]['DIEROUTE_MAX_ITERATIONS']=='30'
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'result.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='two_arm_three_layer_pilot_current_evidence_reviewed',cases=rows,baseline=dict(wirelength=11615,cpd_ns=10.4531,model_crossings=baseline),source_sha256=cache,scope='One run per arm, same fullgraph/placement/nativecost/configuration except backend mode. Current hashes, exact resource replay, tree occupancy, persistent timing provenance and native legal/QoR stdout rechecked. No repetition, representative cohort, scaling, adoption or physical SLL/board proof.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],cases=rows)))
if __name__=='__main__':main()
