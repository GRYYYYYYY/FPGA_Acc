"""Freeze the four-arm fanout-dispatch/whole-net-schedule development experiment."""
import argparse,copy,hashlib,json,shutil
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


DRIVER=r'''import csv,hashlib,json,os,struct,subprocess,sys,traceback
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native_tools'))
from rr_fanout_dispatch_replay import replay
p=json.loads((root/'native_protocol.json').read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify():
 for path,value in p['source_sha256'].items():assert sha(path)==value,path
state=dict(status='starting',pid=os.getpid(),steps=[],board_result=False,research_complete=False)
def save():(root/'native_manifest.json').write_text(json.dumps(state,indent=2)+'\n')
def run(label,cmd):
 row=dict(label=label,command=cmd,status='running');state['steps'].append(row);save()
 with (root/(label+'.log')).open('w') as log:
  child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);row['pid']=child.pid;save();code=child.wait()
 row.update(status='passed' if code==0 else 'failed',returncode=code);save();assert code==0,(label,code)
try:
 verify();out=root/'native_runs';out.mkdir(exist_ok=False);state['status']='running';save()
 build=Path(p['timing_build']);vpr=json.loads((build/'build_dependency_audit.json').read_text())['binary']
 proofs=[];outcomes={}
 for arm,config in p['arms'].items():
  previous=None;original=json.loads(Path(config['parent_pair']).read_text())
  for repeat in range(5):
   verify();name=f'{arm}_{repeat}';directory=out/name;recipe=root/'native_recipes'/arm/'pair.json'
   run(name,[sys.executable,str(root/'native_tools/run_persistent_timing_online.py'),str(recipe),str(build),str(directory)])
   report=json.loads((directory/'route.json').read_text());assert report['legal'] and report['net_dispatch_order']==config['net_order'] and report['ordinary_schedule_mode']==config['schedule']
   assert report['speculative_workers']==0
   report.pop('wall_ms');hashes={path.name:sha(path) for path in directory.glob('route.*') if path.name!='route.json'}
   if previous is not None:assert previous==(report,hashes),(arm,repeat)
   previous=(report,hashes)
   result=replay(Path(p['input_prefix']),directory/'route',config['schedule'],4,3,net_order_mode=config['net_order'])
   assert result['cpu_legal'] and result['final_resources_and_costs_byte_equivalent']
   q=directory/'dispatch_resource_replay_audit.json';q.write_text(json.dumps(result,indent=2)+'\n');proofs.append(q)
   run(name+'_tree',[sys.executable,str(root/'native_tools/audit_rr_final_tree_state.py'),p['input_prefix'],str(directory/'route'),'--report',str(directory/'tree_audit.json')]);proofs.append(directory/'tree_audit.json')
   run(name+'_timing',[sys.executable,str(root/'native_tools/audit_persistent_session_provenance.py'),str(recipe),str(directory)]);proofs.append(directory/'session_provenance_audit.json')
   if config['net_order']==0:
    parent=Path(config['parent_pair']).parent/'downstream_bounded_0';checks=[]
    for source in sorted(parent.parent.glob(parent.name+'.*')):
     suffix=source.name[len(parent.name):]
     if suffix.endswith('.log'):continue
     target=directory/('route'+suffix)
     if suffix=='.json':
      a=json.loads(source.read_text());b=json.loads(target.read_text());a.pop('wall_ms');b.pop('wall_ms');assert b.pop('net_dispatch_order')==0;assert a==b
     else:assert source.read_bytes()==target.read_bytes(),(name,suffix)
     checks.append(dict(suffix=suffix,parent_sha256=sha(source),control_sha256=sha(target)))
    q=directory/'legacy_parent_compatibility.json';q.write_text(json.dumps(dict(status='unchanged_legacy_net_dispatch_matches_completed_reference',checks=checks),indent=2)+'\n');proofs.append(q)
  base=out/f'{arm}_0'
  cmd=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_write')['command']);cmd[-2]=str(base/'route.route_trees.csv');cmd[-1]=str(base/'native.route');run(arm+'_writeback',cmd)
  cmd=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_validate')['command']);cmd[cmd.index('--vpr')+1]=vpr;cmd[cmd.index('--route')+1]=str(base/'native.route');cmd[cmd.index('--work-dir')+1]=str(base/'native_validation');run(arm+'_validate',cmd)
  q=base/'native_validation/validation.json';native=json.loads(q.read_text());assert native['legal'];proofs.append(q)
  owners=[r[0] for r in struct.iter_unpack('<H',Path(p['topology_prefix']+'.node_die').read_bytes())];crossings=set();destinations=set()
  with (base/'route.route_trees.csv').open() as stream:
   for row in csv.DictReader(stream):
    net,parent,child=[int(row[k]) for k in ['net_id','parent','child']]
    if owners[parent]!=owners[child]:crossings.add((net,parent,child));destinations.add((net,child))
  checks=dict(native_legal=native['legal'],wirelength_nondegrade=native['total_wirelength']<=native['baseline_wirelength'],cpd_nondegrade=native['critical_path_delay_ns']<=native['baseline_cpd_ns'],model_crossings_nondegrade=len(crossings)<=p['baseline_model_crossings'])
  outcomes[arm]=dict(native_qor=native,model_crossings=len(crossings),model_destinations=len(destinations),checks=checks,all_ex5p_model_checks_pass=all(checks.values()),configuration=config,counters=json.loads((base/'route.json').read_text()));proofs.extend([base/'route.route_trees.csv',base/'route.json'])
 verify();state['status']='twenty_native_fanout_schedule_runs_and_independent_audits_complete';save()
 proofs.extend([root/'native_manifest.json',root/'native_protocol.json',Path(__file__).resolve()])
 (root/'native_result.json').write_text(json.dumps(dict(status=state['status'],outcomes=outcomes,source_sha256={str(q):sha(q) for q in proofs},scope=p['scope'],adopted=False,board_result=False,research_complete=False),indent=2)+'\n')
except BaseException as error:state.update(status='failed',error=repr(error),traceback=traceback.format_exc());save();raise
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('variant',type=Path);a=parser.parse_args();root=a.variant.resolve()
    assert not (root/'native_protocol.json').exists()
    host=root/'host_controls/audit.json';h=json.loads(host.read_text());assert h['status']=='twenty_actual_fanout_schedule_host_runs_dispatch_and_state_replayed' and len(h['runs'])==20
    sanitizer=root/'sanitizer_actual_host_controls/audit.json';s=json.loads(sanitizer.read_text());assert s['status']=='actual_asan_ubsan_binary_fanout_bulk_and_serial_routes_and_state_replay_pass'
    for proof in [h,s]:
        assert all(sha(path)==value for path,value in proof['source_sha256'].items())
    parents={0:Path('work/rr_pair_ex5p_ordinary_schedule_bulk_v1_20261015/pair.json').resolve(),2:Path('work/rr_pair_ex5p_ordinary_schedule_serial_v1_20261015/pair.json').resolve()}
    original=json.loads(parents[0].read_text());step=next(s for s in original['steps'] if s['label']=='downstream_bounded_0')
    for suffix in ['nodes','edges','resources','tasks']:
        assert sha(parents[0].parent/('input.'+suffix))==sha(parents[2].parent/('input.'+suffix))
    arms={name:dict(schedule=schedule,net_order=order,parent_pair=str(parents[schedule])) for name,schedule,order in [('legacy_bulk',0,0),('fanout_bulk',0,1),('legacy_serial',2,0),('fanout_serial',2,1)]}
    td=root/'native_tools';td.mkdir()
    for name in ['run_persistent_timing_online.py','persistent_timing_client.py','persistent_vpr_timing.py','rr_fanout_dispatch_replay.py','rr_resource_version_replay.py','audit_rr_final_tree_state.py','audit_persistent_session_provenance.py']:
        shutil.copy2(Path(__file__).parent/name,td/name)
    q=td/'audit_persistent_session_provenance.py';text=q.read_text();old="epochs=m['modes'][mode]['runs'][0]['iterations']";assert text.count(old)==1;q.write_text(text.replace(old,"epochs=json.loads((online/'route.json').read_text())['iterations']"))
    files=[host,sanitizer,root/'design_protocol.json',root/'build/dieroute_rr',Path(__file__).resolve(),*parents.values()]
    for arm,config in arms.items():
        directory=root/'native_recipes'/arm;directory.mkdir(parents=True)
        (directory/'source').symlink_to(parents[0].parent/'source',target_is_directory=True);(directory/'input.tasks').symlink_to(parents[0].parent/'input.tasks')
        route=copy.deepcopy(step);route['command'][0]=str(root/'build/dieroute_rr');route['routing_environment'].update(DIEROUTE_ORDINARY_SCHEDULE_MODE=str(config['schedule']),DIEROUTE_NET_DISPATCH_ORDER=str(config['net_order']))
        m=dict(status='frozen',modes={'downstream_bounded':{}},steps=[route],reference=str(parents[config['schedule']]),scope='Sameinput/clock/cost/STApolicy,factorialnetdispatch andordinaryscheduleonly')
        q=directory/'pair.json';q.write_text(json.dumps(m,indent=2)+'\n');files.extend([q,directory/'input.tasks',directory/'source/persistroute/tools/vpr_timing_analyzer.py'])
    build=Path('work/vpr_persistent_timing_build_20261015').resolve();dependency=build/'build_dependency_audit.json';files.extend([dependency,Path(json.loads(dependency.read_text())['binary'])])
    files.extend(p for p in (root/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts);files.extend(p for p in td.iterdir() if p.is_file())
    for prefix in step['command'][1:3]:
        q=Path(prefix);files.extend(q.parent.glob(q.name+'.*'))
    files.extend(Path(original['case'])/name for name in ['architecture.xml','circuit.blif','circuit.net','circuit.place','circuit.route','rr_graph.xml'])
    driver=root/'supervise_native.py';driver.write_text(DRIVER);files.append(driver)
    protocol=dict(schema='dieroute.native_fanout_dispatch_factorial.v1',arms=arms,repeats=5,input_prefix=step['command'][1],topology_prefix=step['command'][2],timing_build=str(build),baseline_model_crossings=484,source_sha256={str(p):sha(p) for p in files},scope='Ex5p-only2x2frozenbaselinepolicycalibration,5actualnative repeatsperarm. Legacycongestionschedule andallotherparametersfixed. Fanoutdispatchversuslegacyorder crossedwithbulkversusserialwholenetprocessing. Bulkbackendprioritywithinbatchpreserved;notcompleteVPRpolicyemulationornewDieRoutealgorithm. Exactdispatch/resource/version/tree/provenance/legacycontrol/nativeQoRandmodelcrossingsrequired;noheldoutopening,gatewaiveroradoptionononecase.',adopted=False,board_result=False,research_complete=False)
    (root/'native_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps(dict(status='fanout_factorial_native_protocol_frozen',arms=arms,files=len(protocol['source_sha256']))))


if __name__=='__main__':main()
