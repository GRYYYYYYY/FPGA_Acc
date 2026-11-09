"""Review all six matched three-layer development runs without accepting illegal QoR."""
import csv,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'work/rr_remaining_tail_precision_development_v2_20261015';cache={}
def sha(q):
 q=str(Path(q).resolve())
 if q not in cache:
  h=hashlib.sha256()
  with Path(q).open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[q]=h.hexdigest()
 return cache[q]
def load(q):return json.loads(Path(q).read_text())
def refs(x):
 for q,h in x.get('source_sha256',{}).items():assert sha(q)==h,q

def main():
 p=load(P/'protocol.json');refs(p);refs(load(P/'launch_protocol.json'));refs(load(P/'runtime_parent_binding.json'));r=load(P/'result.json');refs(r)
 assert r['status']=='six_remaining_tail_precision_development_runs_terminal_and_replayed' and len(r['outcomes'])==6
 expected={(c['label'],a['label']) for c in p['cases'] for a in p['arms']};assert {(v['case'],v['arm']) for v in r['outcomes']}==expected
 rows=[]
 for c in p['cases']:
  owners=[v[0] for v in struct.iter_unpack('<H',Path(c['topology_prefix']+'.node_die').read_bytes())]
  def count(path):
   edges=set()
   for row in csv.DictReader(Path(path).open()):
    n,a,b=(int(row[k]) for k in ['net_id','parent','child']);assert 0<=a<len(owners) and 0<=b<len(owners)
    if owners[a]!=owners[b]:edges.add((n,a,b))
   return len(edges)
  baseline=count(c['native_tree']);environments=[];commands=[]
  native=Path(c['native_case']);native_text=(native/'vpr_stdout.log').read_text()
  assert int(re.findall(r'Total wirelength:\s+(\d+)',native_text)[-1])==c['baseline_wirelength']
  assert float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',native_text)[-1])==c['baseline_cpd_ns']
  for arm in p['arms']:
   row=next(v for v in r['outcomes'] if (v['case'],v['arm'])==(c['label'],arm['label']));refs(row)
   d=P/'native_runs'/(c['label']+'_'+arm['label']+'_0');route=load(d/'route.json');run=load(d/'manifest.json');refs(run)
   recipe=load(P/'recipes'/c['label']/arm['label']/'pair.json')['steps'][0];env=dict(recipe['routing_environment']);assert env.pop('DIEROUTE_REMAINING_LAYER_TAIL')==str(arm['remaining_tail']);assert env.pop('DIEROUTE_TREE_TIMING_WEIGHT_Q')==str(arm['timing_weight']);assert env.pop('DIEROUTE_COST_SCALE')==str(arm['cost_scale']);environments.append(env);commands.append(recipe['command'])
   assert route['mode']==arm['mode'] and bool(route.get('remaining_layer_tail',False))==bool(arm['remaining_tail'])
   assert route['route_tree_timing_weight_q']==arm['timing_weight'] and route['cost_scale']==arm['cost_scale']
   assert route['legal']==row['cpu_legal'] and route['iterations']==row['iterations'] and route['overused_resources']==row['overused_resources']
   replay=load(d/'replay_audit.json');refs(replay);assert replay['requested_cost_scale']==arm['cost_scale'];assert replay['cpu_legal']==route['legal'] and replay['epochs']==route['iterations'] and replay['final_resources_and_costs_byte_equivalent']
   tree=load(d/'tree_audit.json');refs(tree);assert tree['resources']==len(owners)
   resources=list(struct.iter_unpack('<HHHHII',(d/'route.resources').read_bytes()));assert sum(v[0]>v[1] for v in resources)==route['overused_resources']
   crossings=count(d/'route.route_trees.csv');assert crossings==row['model_crossings'] and baseline==row['baseline_model_crossings']
   checks=dict(cpu_legal=route['legal']);q=None
   if route['legal']:
    assert run['returncode']==0 and route['overused_resources']==0
    timing=load(d/'session_provenance_audit.json');refs(timing);assert timing['epochs']==route['iterations']
    q=load(d/'native_validation/validation.json');assert q==row['native_qor'] and q['legal'] and q['vpr_exit_status']==0
    stdout=d/'native_validation/vpr_analysis.stdout';stderr=d/'native_validation/vpr_analysis.stderr';assert sha(stdout)==q['stdout_sha256'] and sha(stderr)==q['stderr_sha256'];text=stdout.read_text()
    for marker in ['Finished loading route file','Completed routing consistency check successfully.','Circuit successfully routed','VPR succeeded']:assert marker in text
    assert int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1])==q['total_wirelength']
    assert float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1])==q['critical_path_delay_ns']
    for key,path in [('vpr',Path(q['command'][0])),('arch',native/'architecture.xml'),('circuit',native/'circuit.blif'),('net',native/'circuit.net'),('place',native/'circuit.place'),('route',d/'native.route'),('rr_graph',native/'rr_graph.xml')]:assert sha(path)==q['inputs'][key+'_sha256']
    assert q['command'][q['command'].index('--device')+1]=='DieRouteSBScale3'
    checks.update(native_legal=True,wirelength_nondegrade=q['total_wirelength']<=c['baseline_wirelength'],cpd_nondegrade=q['critical_path_delay_ns']<=c['baseline_cpd_ns'])
   else:
    assert route['iterations']==30 and route['overused_resources']>0 and row['native_qor'] is None and run['error']=='AssertionError((3, []))' and run['server_errors']==[]
    assert not tree['cpu_legal'] and tree['overused_resources']==route['overused_resources']
   checks['model_crossings_nondegrade']=crossings<=baseline;assert checks==row['checks'] and all(checks.values())==row['joint_gate_pass']
   if arm['cost_scale']==1:
    compatibility=load(d/'parent_scale1_compatibility.json');assert compatibility['status']=='fresh_remaining_tail_scale1_matches_completed_parent';parent=Path(c['parent_prefix'])
    for comparison in compatibility['comparisons']:
     suffix=comparison['suffix'];source=Path(str(parent)+suffix);target=d/('route'+suffix)
     assert sha(source)==comparison['parent_sha256'] and sha(target)==comparison['control_sha256']
     if suffix=='.json':
      first=load(source);second=load(target);first.pop('wall_ms');second.pop('wall_ms');assert first==second
     else:assert source.read_bytes()==target.read_bytes()
    sha(d/'parent_scale1_compatibility.json')
   rows.append(dict(case=c['label'],arm=arm['label'],cpu_legal=route['legal'],iterations=route['iterations'],overused_resources=route['overused_resources'],model_crossings=crossings,baseline_model_crossings=baseline,wirelength=q['total_wirelength'] if q else None,cpd_ns=q['critical_path_delay_ns'] if q else None,checks=checks,joint_gate_pass=all(checks.values())))
  assert all(e==environments[0] for e in environments) and all(cmd[:-1]==commands[0][:-1] for cmd in commands)
 for q in [P/'result.json',P/'manifest.json',P/'protocol.json',P/'launch_protocol.json',P/'runtime_parent_binding.json',Path(__file__).resolve()]:sha(q)
 report=dict(status='six_remaining_tail_precision_development_runs_independently_reviewed',outcomes=rows,source_sha256=cache,scope='Sixactualruns,threefixeddeclareddevelopmentcasesxcostscale1/256seed128withremainingtailenabled,onerepeateach;freshscale1controlsrecomparedwithcompletedparents. Currentinput/artifacthashes,exactresource/version/costreplay,treeoccupancyandnativelegal/printedQoRrechecked. Expectedmax30capacityfailureskeptnonlegalandwithoutnativeQoR. Noallcaseimprovement,repeat,heldout,adoptionorphysicalclaim.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=rows)))
if __name__=='__main__':main()
