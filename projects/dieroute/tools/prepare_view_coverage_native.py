"""Freeze matched native explicit-view-census off/on runs with read observations enabled."""
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
from rr_transfer_seed_replay import replay as seed_replay
from rr_adaptive_policy_replay import replay
from rr_observed_read_replay import replay as read_replay
from audit_adaptive_task_events import audit
from audit_view_access_coverage import audit as coverage_audit
p=json.loads((root/'native_protocol.json').read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()
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
            report=json.loads((directory/'route.json').read_text());assert report['legal'] and report['task_placement_mode']==config['placement'] and report['present_schedule_mode']==0 and report['speculative_workers']==2
            report.pop('wall_ms');hashes={path.name:sha(path) for path in directory.glob('route.*') if path.name!='route.json'}
            if previous is not None:assert previous==(report,hashes),(arm,repeat)
            previous=(report,hashes)
            state_proof=(replay(Path(p['input_prefix']),directory/'route',0,4,3,topology_prefix=Path(p['topology_prefix']),workers=2) if config['placement']==3 else seed_replay(Path(p['input_prefix']),directory/'route',0,4,3))
            assert state_proof['received_task_requests_checked']>0 and state_proof['received_seed_rows_checked']>=state_proof['received_task_requests_checked']
            if config['record']:
                reads=read_replay(Path(p['input_prefix']),directory/'route',0,4,3,topology_prefix=Path(p['topology_prefix']),workers=2,shadow_sync=config['sync'])
                assert reads['observed_read_rows_checked']==report['speculative_read_entries'] and reads['remote_shadow_rows_checked']==report['remote_shadow_reads'] and reads['fresh_replays_checked']==report['speculative_replays']
                q=directory/'observed_read_audit.json';q.write_text(json.dumps(reads,indent=2)+'\n');proofs.append(q)
                if config['coverage']:
                    coverage=coverage_audit(Path(p['input_prefix']),Path(p['topology_prefix']),directory/'route')
                    assert coverage['unique_node_occurrences']==reads['observed_read_rows_checked']
                    q=directory/'view_coverage_audit.json';q.write_text(json.dumps(coverage,indent=2)+'\n');proofs.append(q)
            state_path=directory/'resource_replay_audit.json';state_path.write_text(json.dumps(state_proof,indent=2)+'\n');proofs.append(state_path)
            if config['slots']:
                credit=audit(Path(p['input_prefix']),Path(p['topology_prefix']),directory/'route',config['slots'],config['bytes'],config['placement'])
                if config['placement']==2:assert credit['events']['backpressure']>0
                else:assert credit['decision_requests_checked']==state_proof['adaptive_decisions_checked']
                q=directory/'credit_replay_audit.json';q.write_text(json.dumps(credit,indent=2)+'\n');proofs.append(q)
            run(name+'_tree',[sys.executable,str(root/'native_tools/audit_rr_final_tree_state.py'),p['input_prefix'],str(directory/'route'),'--report',str(directory/'tree_audit.json')]);proofs.append(directory/'tree_audit.json')
            run(name+'_timing',[sys.executable,str(root/'native_tools/audit_persistent_session_provenance.py'),str(recipe),str(directory)]);proofs.append(directory/'session_provenance_audit.json')
            if config['coverage']:
                parent=out/f'control_{repeat}'/'route';comparisons=[]
                for source in sorted(parent.parent.glob(parent.name+'.*')):
                    suffix=source.name[len(parent.name):];target=directory/('route'+suffix)
                    if suffix=='.json':
                        a=json.loads(source.read_text());b=json.loads(target.read_text());a.pop('wall_ms');b.pop('wall_ms');assert a==b
                    else:assert sha(source)==sha(target),(name,suffix)
                    comparisons.append(dict(suffix=suffix,control_sha256=sha(source),observed_sha256=sha(target)))
                q=directory/'control_compatibility.json';q.write_text(json.dumps(dict(status='all_actual_route_artifacts_match_same_binary_observation_disabled',checks=comparisons),indent=2)+'\n');proofs.append(q)
        base=out/f'{arm}_0'
        command=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_write')['command']);command[-2]=str(base/'route.route_trees.csv');command[-1]=str(base/'native.route');run(arm+'_writeback',command)
        command=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_validate')['command']);command[command.index('--vpr')+1]=vpr;command[command.index('--route')+1]=str(base/'native.route');command[command.index('--work-dir')+1]=str(base/'native_validation');run(arm+'_validate',command)
        q=base/'native_validation/validation.json';validation=json.loads(q.read_text());assert validation['legal'];proofs.append(q)
        outcomes[arm]=dict(native_qor=validation,configuration=config,counters=json.loads((base/'route.json').read_text()))
    verify();state['status']='ten_native_view_access_coverage_runs_and_independent_audits_complete';save()
    proofs.extend([root/'native_manifest.json',root/'native_protocol.json',Path(__file__).resolve()])
    (root/'native_result.json').write_text(json.dumps(dict(status=state['status'],outcomes=outcomes,source_sha256={str(f):sha(f) for f in proofs},scope=p['scope'],adopted=False,board_result=False,research_complete=False),indent=2)+'\n')
except BaseException as error:state.update(status='failed',error=repr(error),traceback=traceback.format_exc());save();raise
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('variant',type=Path);a=parser.parse_args()
    root=a.variant.resolve();assert not (root/'native_protocol.json').exists()
    host_audit=root/'host_controls/audit.json'
    host=json.loads(host_audit.read_text());assert host['status']=='twenty_actual_host_independent_view_censuses_and_read_journals_checked' and len(host['runs'])==20
    assert all(sha(path)==value for path,value in host['source_sha256'].items())
    assert '100% tests passed' in (root/'component_test.log').read_text()
    assert (root/'sanitizer_test.log').read_text().strip()=='speculative_backend_tb PASS'
    failed_path=root/'failed_task_controls/audit.json'
    failed=json.loads(failed_path.read_text());assert failed['status']=='actual_failed_searches_dual_view_census_journal_and_stale_replay_checked'
    assert failed['replay']['fresh_replays_checked']==2 and failed['replay']['accepted_connections']==0
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
    arms=dict(control=dict(slots=1,bytes=16777216,placement=3,sync=3,record=1,coverage=0),covered=dict(slots=1,bytes=16777216,placement=3,sync=3,record=1,coverage=1))
    td=root/'native_tools';td.mkdir()
    for name in ['run_persistent_timing_online.py','persistent_timing_client.py','persistent_vpr_timing.py',
                 'rr_transfer_seed_replay.py','rr_adaptive_policy_replay.py','rr_observed_read_replay.py','audit_view_access_coverage.py','rr_resource_version_replay.py','audit_adaptive_task_events.py',
                 'audit_rr_final_tree_state.py','audit_persistent_session_provenance.py']:
        shutil.copy2(Path(__file__).parent/name,td/name)
    prov=td/'audit_persistent_session_provenance.py';text=prov.read_text();old="epochs=m['modes'][mode]['runs'][0]['iterations']";assert text.count(old)==1;prov.write_text(text.replace(old,"epochs=json.loads((online/'route.json').read_text())['iterations']"))
    files=[host_audit,failed_path,root/'component_test.log',root/'sanitizer_test.log',root/'build/dieroute_rr',parent,
           static/'result.json',trace,Path(__file__).resolve(),root/'protocol.json']
    for arm,config in arms.items():
        rp=root/'native_recipes'/arm;rp.mkdir(parents=True);(rp/'source').symlink_to((parent.parent/'source').resolve(),target_is_directory=True);(rp/'input.tasks').symlink_to((parent.parent/'input.tasks').resolve())
        m=copy.deepcopy(recipe);s=m['steps'][0];s['command'][0]=str(root/'build/dieroute_rr');s['routing_environment'].update(DIEROUTE_AUDIT_READ_COVERAGE=str(config['coverage']),DIEROUTE_RECORD_READ_VALUES=str(config['record']),DIEROUTE_SHADOW_SYNC_WINDOWS=str(config['sync']),DIEROUTE_TASK_PLACEMENT_MODE=str(config['placement']),DIEROUTE_TASK_TRANSFER_SLOTS=str(config['slots']),DIEROUTE_TASK_TRANSFER_BYTES=str(config['bytes']))
        (rp/'pair.json').write_text(json.dumps(m,indent=2)+'\n');files.extend([rp/'pair.json',rp/'input.tasks',rp/'source/persistroute/tools/vpr_timing_analyzer.py'])
    original=Path(recipe['reference']);original_record=json.loads(original.read_text());files.append(original)
    build=Path('work/vpr_persistent_timing_build_20261015').resolve();dependency=build/'build_dependency_audit.json';files.extend([dependency,Path(json.loads(dependency.read_text())['binary'])])
    files.extend(p for p in (root/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend(p for p in td.iterdir() if p.is_file())
    for prefix in recipe['steps'][0]['command'][1:3]:
        path=Path(prefix);files.extend(path.parent.glob(path.name+'.*'))
    files.extend(Path(original_record['case'])/name for name in ['architecture.xml','circuit.blif','circuit.net','circuit.place','circuit.route','rr_graph.xml'])
    driver=root/'supervise_native.py';driver.write_text(DRIVER);files.append(driver)
    p=dict(schema='dieroute.native_view_access_coverage_study.v1',arms=arms,repeats=5,original_pair=str(original),
        input_prefix=recipe['steps'][0]['command'][1],topology_prefix=recipe['steps'][0]['command'][2],
        static_parent_prefix=str(static/'native_runs_v2/mode2_0/route'),timing_build=str(build),
        byte_capacity_choice=dict(rule='max encoded message size in completed static destination trace;no candidate QoR tuning',bytes=limit,expected_overlapping_byte_pressure_windows=pressure),
        source_sha256={str(path):sha(path) for path in files},
        scope='MatchedexplicitviewAPIcensusoff/on,valuerecordingenabledbotharms,samefrozenReleasebinary/adaptive3/entrycredit1/sync3,5nativeex5prepeats each. Independentviewnodecensus versusjournal,pernode/globalcounts;authority/shadowvalue/stalereplay,pressure,credits,seeds,tree,provenance/nativeQoR andsamebinarycontrolartifacthashes checked. APIcallcoverageonly,notgeneralpointer-memorytracing,searchoptimalityorhardwareperformance;diagnosticcostcallsincluded.',
        adopted=False,board_result=False,research_complete=False)
    (root/'native_protocol.json').write_text(json.dumps(p,indent=2)+'\n')
    print(json.dumps(dict(status='native_view_coverage_study_frozen',arms=arms,byte_pressure_windows=pressure,frozen_files=len(p['source_sha256']))))


if __name__=='__main__':main()
