"""Freeze an initial-criticality-only, five-repeat paired development experiment."""
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


SUPERVISOR = r'''import csv, hashlib, json, os, subprocess, sys, traceback
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'tools'))
from rr_present_schedule_replay import replay
protocol=json.loads((root/'protocol.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
    for name,expected in protocol['source_sha256'].items():
        assert sha(name)==expected,('frozen input changed',name)
state=dict(status='starting',pid=os.getpid(),steps=[],board_result=False,research_complete=False)
def save():(root/'manifest.json').write_text(json.dumps(state,indent=2)+'\n')
def run(label,command):
    step=dict(label=label,command=command,status='running');state['steps'].append(step);save()
    with (root/(label+'.log')).open('w') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);step['pid']=proc.pid;save();code=proc.wait()
    step.update(status='passed' if code==0 else 'failed',returncode=code);save()
    assert code==0,(label,code)
try:
    verify();output=root/'runs';output.mkdir(exist_ok=False);state['status']='running';save()
    original=json.loads(Path(protocol['parent_pair']).read_text())
    build=Path(protocol['timing_build']);binary=json.loads((build/'build_dependency_audit.json').read_text())['binary']
    seen={};proofs=[]
    for repeat in range(5):
        for arm in (['uniform','native'] if repeat%2==0 else ['native','uniform']):
            verify();name=f'{arm}_{repeat}';directory=output/name;recipe=root/'recipes'/arm/'pair.json'
            run(name,[sys.executable,str(root/'tools/run_persistent_timing_online.py'),str(recipe),str(build),str(directory)])
            report=json.loads((directory/'route.json').read_text());assert report['legal']
            assert report['present_schedule_mode']==2 and report['speculative_workers']==0 and report['ordinary_schedule_mode']==0
            report.pop('wall_ms');hashes={p.name:sha(p) for p in sorted(directory.glob('route.*')) if p.name!='route.json'}
            if arm in seen:assert (report,hashes)==seen[arm],('nondeterministic',name)
            seen[arm]=(report,hashes)
            replay_result=replay(root/'recipes'/arm/'input',directory/'route',0,4,3,present_mode=2)
            audit_path=directory/'resource_replay_audit.json';audit_path.write_text(json.dumps(dict(status='all_initial_and_updated_criticalities_controller_resources_and_versions_replayed',result=replay_result),indent=2)+'\n');proofs.append(audit_path)
            run(name+'_tree',[sys.executable,str(root/'tools/audit_rr_final_tree_state.py'),str(root/'recipes'/arm/'input'),str(directory/'route'),'--report',str(directory/'final_tree_state_audit.json')])
            proofs.append(directory/'final_tree_state_audit.json')
            run(name+'_timing_provenance',[sys.executable,str(root/'tools/audit_persistent_session_provenance.py'),str(recipe),str(directory)])
            proofs.append(directory/'session_provenance_audit.json')
            if arm=='uniform':
                checks=[];parent=Path(protocol['parent_pair']).parent
                for source in sorted(parent.glob('downstream_bounded_0.*')):
                    suffix=source.name[len('downstream_bounded_0'):]
                    if suffix.endswith('.log'):continue
                    target=directory/('route'+suffix);assert target.is_file()
                    if suffix=='.json':
                        a=json.loads(source.read_text());b=json.loads(target.read_text());a.pop('wall_ms');b.pop('wall_ms');assert a==b
                    else:assert source.read_bytes()==target.read_bytes(),suffix
                    checks.append(dict(suffix=suffix,parent_sha256=sha(source),control_sha256=sha(target)))
                p=directory/'parent_compatibility.json';p.write_text(json.dumps(dict(status='uniform_control_matches_frozen_positive_reference',checks=checks),indent=2)+'\n');proofs.append(p)
    outcomes={}
    for arm in ['uniform','native']:
        base=output/f'{arm}_0'
        command=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_write')['command'])
        command[-2]=str(base/'route.route_trees.csv');command[-1]=str(base/'native.route')
        run(arm+'_writeback',command)
        command=list(next(s for s in original['steps'] if s['label']=='downstream_bounded_validate')['command'])
        command[command.index('--vpr')+1]=binary;command[command.index('--route')+1]=str(base/'native.route');command[command.index('--work-dir')+1]=str(base/'native_validation')
        run(arm+'_validate',command)
        p=base/'native_validation/validation.json';q=json.loads(p.read_text());assert q['legal'];proofs.append(p)
        import struct
        owners=[r[0] for r in struct.iter_unpack('<H',Path(protocol['topology_prefix']+'.node_die').read_bytes())]
        crossings=set();destinations=set()
        with (base/'route.route_trees.csv').open() as stream:
            for row in csv.DictReader(stream):
                net,parent,child=[int(row[k]) for k in ['net_id','parent','child']]
                if owners[parent]!=owners[child]:crossings.add((net,parent,child));destinations.add((net,child))
        checks=dict(native_legal=q['legal'],wirelength_nondegrade=q['total_wirelength']<=q['baseline_wirelength'],cpd_nondegrade=q['critical_path_delay_ns']<=q['baseline_cpd_ns'],model_crossings_nondegrade=len(crossings)<=protocol['baseline_model_crossings'])
        outcomes[arm]=dict(native_qor=q,counters=json.loads((base/'route.json').read_text()),model_crossings=len(crossings),model_destinations=len(destinations),checks=checks,all_ex5p_model_checks_pass=all(checks.values()))
        proofs.extend([base/'route.route_trees.csv',base/'route.json'])
    verify();state['status']='ten_initial_criticality_runs_native_validations_and_independent_audits_complete';save()
    proofs.extend([root/'protocol.json',root/'manifest.json',Path(__file__).resolve()])
    (root/'result.json').write_text(json.dumps(dict(status=state['status'],outcomes=outcomes,source_sha256={str(p):sha(p) for p in proofs},scope=protocol['scope'],adopted=False,board_result=False,research_complete=False),indent=2)+'\n')
except BaseException as error:
    state.update(status='failed',error=repr(error),traceback=traceback.format_exc());save();raise
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent_pair', type=Path)
    parser.add_argument('joined', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    parent_pair, joined, output = [p.resolve() for p in (args.parent_pair, args.joined, args.output)]
    assert not output.exists()
    parent = json.loads(parent_pair.read_text())
    proof = json.loads((joined / 'audit.json').read_text())
    assert proof['status'] == 'native_initial_timing_joined_by_logical_pin_and_task_only_candidate_prepared'
    assert proof['source_sha256'][str(parent_pair)] == sha(parent_pair)
    for key in ['source_sha256', 'output_sha256']:
        for name, expected in proof[key].items():
            assert sha(name) == expected, name
    step = next(s for s in parent['steps'] if s['label'] == 'downstream_bounded_0')
    assert sha(step['command'][0]) == parent['binary_sha256']
    for name, expected in parent['source_sha256'].items():
        assert sha(parent_pair.parent / name) == expected, name
    output.mkdir()
    tools_dir = output / 'tools'
    tools_dir.mkdir()
    for name in ['run_persistent_timing_online.py', 'persistent_timing_client.py', 'persistent_vpr_timing.py',
                 'rr_present_schedule_replay.py', 'rr_resource_version_replay.py',
                 'audit_rr_final_tree_state.py', 'audit_persistent_session_provenance.py']:
        shutil.copy2(Path(__file__).parent / name, tools_dir / name)
    # A fresh recipe has no historical run count: bind epochs to the actual completed router.
    provenance = tools_dir / 'audit_persistent_session_provenance.py'
    text = provenance.read_text()
    old = "epochs=m['modes'][mode]['runs'][0]['iterations']"
    assert text.count(old) == 1
    provenance.write_text(text.replace(old, "epochs=json.loads((online/'route.json').read_text())['iterations']"))
    files = [parent_pair, joined / 'audit.json', joined / 'mutation_audit.json', joined / 'native_initial.tasks',
             Path(step['command'][0]), Path(__file__).resolve()]
    files.extend(parent_pair.parent / name for name in parent['source_sha256'])
    for arm in ['uniform', 'native']:
        recipe = output / 'recipes' / arm
        recipe.mkdir(parents=True)
        (recipe / 'source').symlink_to(parent_pair.parent / 'source', target_is_directory=True)
        for path in parent_pair.parent.glob('input.*'):
            if path.suffix == '.tasks':
                shutil.copy2(joined / 'native_initial.tasks' if arm == 'native' else path, recipe / path.name)
            else:
                (recipe / path.name).symlink_to(path)
            files.append(recipe / path.name)
        m = dict(schema='dieroute.initial_criticality_recipe.v1', case=parent['case'], reference=parent['reference'],
                 modes={'downstream_bounded': {}}, configuration=copy.deepcopy(parent['configuration']))
        m['configuration']['initial_criticality_q'] = 'observed_native_per_task' if arm == 'native' else 32768
        routing = copy.deepcopy(step)
        routing['command'][1] = str(recipe / 'input')
        for key in ['status', 'pid', 'returncode', 'elapsed_ns', 'log_sha256']:
            routing.pop(key, None)
        m['steps'] = [routing]
        p = recipe / 'pair.json'
        p.write_text(json.dumps(m, indent=2) + '\n')
        files.append(p)
    build = Path('work/vpr_persistent_timing_build_20261015').resolve()
    dependency = build / 'build_dependency_audit.json'
    files.extend([dependency, Path(json.loads(dependency.read_text())['binary'])])
    files.extend(Path(step['command'][2]).parent.glob(Path(step['command'][2]).name + '.*'))
    files.extend(Path(parent['case']) / name for name in ['architecture.xml', 'circuit.blif', 'circuit.net', 'circuit.place', 'circuit.route', 'rr_graph.xml'])
    files.extend(p for p in tools_dir.iterdir() if p.is_file())
    supervisor = output / 'supervise.py'
    supervisor.write_text(SUPERVISOR)
    files.append(supervisor)
    protocol = dict(schema='dieroute.initial_criticality_study.v1', parent_pair=str(parent_pair),
        timing_build=str(build), topology_prefix=step['command'][2], repeats_per_arm=5,
        arm_order='alternating uniform/native then native/uniform; all five paired repeats retained',
        only_routing_change='initial Task.criticality_q from observed native pre-routing float values',
        later_STA_policy='unchanged raw criticality clamped to 64880; no repeated downward shift',
        configuration=parent['configuration'], baseline_model_crossings=484,
        acceptance='Native legality and exact WL/CPD nondegradation vs frozen strong baseline, plus model crossing count; no threshold relaxation or heldout tuning.',
        source_sha256={str(p): sha(p) for p in files},
        scope='Ex5p-only controlled initialization ablation. Same frozen release router binary, topology, '
              'present preset2 and persistent timing service. Five repeats per arm, exact resource/version '
              'replay and final trees, unchanged uniform positive reference, native validation. '
              'Model crossings are not physical SLL; CPU lifecycle timings not board performance. '
              'No adoption or full DieRoute acceptance inferred from this development study.',
        board_result=False, research_complete=False)
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps(dict(status='initial_criticality_pair_frozen_ready_to_run', output=str(output), frozen_files=len(protocol['source_sha256']))))


if __name__ == '__main__':
    main()
