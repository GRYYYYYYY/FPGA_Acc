"""Freeze five native receiver-seed observations with independent tree reconstruction."""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import shutil


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


DRIVER = r'''import csv,hashlib,json,os,subprocess,sys,traceback
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'native_tools'))
from rr_transfer_seed_replay import replay
from audit_task_credit_events import audit
p=json.loads((root/'native_protocol.json').read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify():
    for path,value in p['source_sha256'].items():assert sha(path)==value,path
state=dict(status='starting',pid=os.getpid(),steps=[],board_result=False,research_complete=False)
def save():(root/'native_manifest.json').write_text(json.dumps(state,indent=2)+'\n')
def run(label,cmd):
    row=dict(label=label,command=cmd,status='running');state['steps'].append(row);save()
    with (root/(label+'.log')).open('w') as log:
        child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);row['pid']=child.pid;save();rc=child.wait()
    row.update(returncode=rc,status='passed' if rc==0 else 'failed');save();assert rc==0,(label,rc)
try:
    verify();out=root/'native_runs';out.mkdir(exist_ok=False);state['status']='running';save()
    build=Path(p['timing_build']);vpr=json.loads((build/'build_dependency_audit.json').read_text())['binary']
    original=json.loads(Path(p['original_pair']).read_text());proofs=[];outcomes={}
    for arm,config in p['arms'].items():
        previous=None
        for repeat in range(5):
            name=f'{arm}_{repeat}';directory=out/name;recipe=root/'native_recipes'/arm/'pair.json'
            verify();run(name,[sys.executable,str(root/'native_tools/run_persistent_timing_online.py'),str(recipe),str(build),str(directory)])
            report=json.loads((directory/'route.json').read_text());assert report['legal'] and report['task_placement_mode']==2 and report['present_schedule_mode']==0 and report['speculative_workers']==2
            report.pop('wall_ms');hashes={path.name:sha(path) for path in directory.glob('route.*') if path.name!='route.json'}
            if previous is not None:assert previous==(report,hashes),(arm,repeat)
            previous=(report,hashes)
            state_proof=replay(Path(p['input_prefix']),directory/'route',0,4,3)
            assert state_proof['received_task_requests_checked']>0 and state_proof['received_seed_rows_checked']>=state_proof['received_task_requests_checked']
            state_path=directory/'resource_replay_audit.json';state_path.write_text(json.dumps(state_proof,indent=2)+'\n');proofs.append(state_path)
            if config['slots']:
                credit=audit(Path(p['input_prefix']),Path(p['topology_prefix']),directory/'route',config['slots'],config['bytes'],2)
                assert credit['events']['backpressure']>0
                q=directory/'credit_replay_audit.json';q.write_text(json.dumps(credit,indent=2)+'\n');proofs.append(q)
            run(name+'_tree',[sys.executable,str(root/'native_tools/audit_rr_final_tree_state.py'),p['input_prefix'],str(directory/'route'),'--report',str(directory/'tree_audit.json')]);proofs.append(directory/'tree_audit.json')
            run(name+'_timing',[sys.executable,str(root/'native_tools/audit_persistent_session_provenance.py'),str(recipe),str(directory)]);proofs.append(directory/'session_provenance_audit.json')
            # Exact route/cost/STA/transaction compatibility to completed static destination study.
            parent=Path(p['static_parent_prefix']);comparisons=[]
            for source in sorted(parent.parent.glob(parent.name+'.*')):
                suffix=source.name[len(parent.name):]
                if suffix.endswith('.log'):continue
                target=directory/('route'+suffix)
                if suffix=='.json':
                    a=json.loads(source.read_text());b=json.loads(target.read_text());a.pop('wall_ms');b.pop('wall_ms');assert a==b
                elif suffix=='.task_migration.csv':
                    with source.open() as stream:a=list(csv.DictReader(stream))
                    with target.open() as stream:b=list(csv.DictReader(stream))
                    assert len(a)==len(b)
                    for x,y in zip(a,b):
                        assert int(y.pop('encoded_envelope_bytes'))==int(x.pop('logical_envelope_bytes'))+28
                        assert x==y
                else:assert source.read_bytes()==target.read_bytes(),(name,suffix)
                comparisons.append(dict(suffix=suffix,parent_sha256=sha(source),candidate_sha256=sha(target)))
            q=directory/'static_parent_compatibility.json';q.write_text(json.dumps(dict(status='all_core_artifacts_match_completed_static_destination_control',checks=comparisons),indent=2)+'\n');proofs.append(q)
        base=out/f'{arm}_0'
        command=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_write')['command']);command[-2]=str(base/'route.route_trees.csv');command[-1]=str(base/'native.route');run(arm+'_writeback',command)
        command=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_validate')['command']);command[command.index('--vpr')+1]=vpr;command[command.index('--route')+1]=str(base/'native.route');command[command.index('--work-dir')+1]=str(base/'native_validation');run(arm+'_validate',command)
        q=base/'native_validation/validation.json';validation=json.loads(q.read_text());assert validation['legal'];proofs.append(q)
        outcomes[arm]=dict(native_qor=validation,configuration=config,counters=json.loads((base/'route.json').read_text()))
    verify();state['status']='five_native_receiver_seed_runs_and_independent_audits_complete';save()
    proofs.extend([root/'native_manifest.json',root/'native_protocol.json',Path(__file__).resolve()])
    (root/'native_result.json').write_text(json.dumps(dict(status=state['status'],outcomes=outcomes,source_sha256={str(f):sha(f) for f in proofs},scope=p['scope'],adopted=False,board_result=False,research_complete=False),indent=2)+'\n')
except BaseException as error:state.update(status='failed',error=repr(error),traceback=traceback.format_exc());save();raise
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('variant',type=Path);a=parser.parse_args()
    root=a.variant.resolve();assert not (root/'native_protocol.json').exists()
    host_audit=root/'host_controls/audit.json'
    host=json.loads(host_audit.read_text());assert host['status']=='actual_receiver_seed_host_controls_and_independent_replay_complete' and len(host['runs'])==35
    assert all(sha(path)==value for path,value in host['source_sha256'].items())
    assert '100% tests passed' in (root/'component_test.log').read_text()
    assert (root/'sanitizer_test.log').read_text().strip()=='speculative_backend_tb PASS'
    failed_path=root/'failed_task_controls/audit.json'
    failed=json.loads(failed_path.read_text())
    assert failed['status']=='actual_failed_tasks_all_receiver_seeds_and_released_credits_replayed'
    assert failed['seed_replay']['received_seed_rows_checked']==3 and failed['seed_replay']['accepted_connections']==0
    assert all(sha(path)==value for path,value in failed['source_sha256'].items())
    static=Path('work/rr_task_migration_variant_20261015').resolve()
    result=json.loads((static/'result.json').read_text());assert result['status']=='fifteen_static_observer_placement_runs_and_native_quality_audited'
    parent=static/'native_recipes_v2/mode2/pair.json';recipe=json.loads(parent.read_text())
    trace=static/'native_runs_v2/mode2_0/route.task_migration.csv'
    with trace.open() as stream:rows=list(csv.DictReader(stream))
    limit=max(60+12*int(r['seed_count']) for r in rows)
    groups={}
    for row in rows:groups.setdefault((row['window'],row['execution_die']),[]).append(60+12*int(row['seed_count']))
    pressure=sum(sum(v)>limit for v in groups.values());assert pressure>0
    arms=dict(received_credit=dict(slots=1,bytes=16777216))
    td=root/'native_tools';td.mkdir()
    for name in ['run_persistent_timing_online.py','persistent_timing_client.py','persistent_vpr_timing.py',
                 'rr_transfer_seed_replay.py','rr_resource_version_replay.py','audit_task_credit_events.py',
                 'audit_rr_final_tree_state.py','audit_persistent_session_provenance.py']:
        shutil.copy2(Path(__file__).parent/name,td/name)
    prov=td/'audit_persistent_session_provenance.py';text=prov.read_text();old="epochs=m['modes'][mode]['runs'][0]['iterations']";assert text.count(old)==1;prov.write_text(text.replace(old,"epochs=json.loads((online/'route.json').read_text())['iterations']"))
    files=[host_audit,failed_path,root/'component_test.log',root/'sanitizer_test.log',root/'build/dieroute_rr',parent,
           static/'result.json',trace,Path(__file__).resolve(),root/'protocol.json']
    for arm,config in arms.items():
        rp=root/'native_recipes'/arm;rp.mkdir(parents=True);(rp/'source').symlink_to((parent.parent/'source').resolve(),target_is_directory=True);(rp/'input.tasks').symlink_to((parent.parent/'input.tasks').resolve())
        m=copy.deepcopy(recipe);s=m['steps'][0];s['command'][0]=str(root/'build/dieroute_rr');s['routing_environment'].update(DIEROUTE_TASK_TRANSFER_SLOTS=str(config['slots']),DIEROUTE_TASK_TRANSFER_BYTES=str(config['bytes']))
        (rp/'pair.json').write_text(json.dumps(m,indent=2)+'\n');files.extend([rp/'pair.json',rp/'input.tasks',rp/'source/persistroute/tools/vpr_timing_analyzer.py'])
    original=Path(recipe['reference']);original_record=json.loads(original.read_text());files.append(original)
    build=Path('work/vpr_persistent_timing_build_20261015').resolve();dependency=build/'build_dependency_audit.json';files.extend([dependency,Path(json.loads(dependency.read_text())['binary'])])
    files.extend(p for p in (root/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend(p for p in td.iterdir() if p.is_file())
    for prefix in recipe['steps'][0]['command'][1:3]:
        path=Path(prefix);files.extend(path.parent.glob(path.name+'.*'))
    files.extend(Path(original_record['case'])/name for name in ['architecture.xml','circuit.blif','circuit.net','circuit.place','circuit.route','rr_graph.xml'])
    driver=root/'supervise_native.py';driver.write_text(DRIVER);files.append(driver)
    p=dict(schema='dieroute.native_received_seed_study.v1',arms=arms,repeats=5,original_pair=str(original),
        input_prefix=recipe['steps'][0]['command'][1],topology_prefix=recipe['steps'][0]['command'][2],
        static_parent_prefix=str(static/'native_runs_v2/mode2_0/route'),timing_build=str(build),
        byte_capacity_choice=dict(rule='max encoded message size in completed static destination trace;no candidate QoR tuning',bytes=limit,expected_overlapping_byte_pressure_windows=pressure),
        source_sha256={str(path):sha(path) for path in files},
        scope='One destination-placement single-credit configuration,5actualnativeex5prepeats. Everydecodedseed includingunusedones reconstructedfromcontroller trees+STA. Fullresource/version/credit/tree/provenance/staticparent audits andnativelegality/QoR. Doesnotcover everycreditsetting,speculativereadsets,adaptivepolicyorhardware;staticparentqualitygatealreadyfails.',
        adopted=False,board_result=False,research_complete=False)
    (root/'native_protocol.json').write_text(json.dumps(p,indent=2)+'\n')
    print(json.dumps(dict(status='native_receiver_seed_study_frozen',arms=arms,byte_pressure_windows=pressure,frozen_files=len(p['source_sha256']))))


if __name__=='__main__':main()
