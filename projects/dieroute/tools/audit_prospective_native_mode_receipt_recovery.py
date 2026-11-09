"""Join ranked native acceptance, sink-order and exact final wirelength checks."""
from pathlib import Path
import array
import collections
import csv
import hashlib
import json
import subprocess
import sys


def main():
    directory = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((directory / 'protocol.json').read_text())
    manifest = json.loads((directory / 'manifest.json').read_text())
    assert manifest['status'].startswith('experiment_terminal_')
    mode = protocol['prospective_mode']
    assert mode in ['wirelength', 'delay']
    tools = ['audit_ranked_critical_native_refinement.py', 'audit_ranked_critical_refinement_policy.py']
    if mode == 'wirelength':
        tools.append('audit_exact_wirelength_refinement.py')
    for name in tools:
        with (directory / (name + '.recovered.log')).open('x') as stream:
            subprocess.run(['python3', str(root / 'tools' / name), str(directory)], cwd=root,
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
    refs = {}

    def read(path):
        path = Path(path)
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    checks = {'target_orders': 0, 'native_wirelengths': 0, 'all_unique_candidate_audits_present': 0}
    for record in manifest['stages']:
        stage = directory / ('stage_' + str(record['iteration']).zfill(3))
        ep_file = stage / 'exchange/protocol.json'
        if not ep_file.exists():
            continue
        ep = read(ep_file)
        assert ep['search_objective'] == mode and ep['reverse_target_remaining_sinks'] is True
        raw = Path(ep['wirelength_weights']).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == ep['source_sha256'][ep['wirelength_weights']]
        refs[ep['wirelength_weights']] = digest
        weights = array.array('H')
        weights.frombytes(raw)
        if sys.byteorder != 'little':
            weights.byteswap()
        tasks = collections.defaultdict(list)
        with Path(ep['connections']).open() as stream:
            for row in csv.DictReader(stream):
                tasks[int(row['net_id'])].append(int(row['id']))
        with Path(ep['native_parent_observations']).open() as stream:
            criticality = {int(row['task_id']): int(row['criticality_q']) for row in csv.DictReader(stream)}
        configs = {a['name']: a for a in ep['arms']}
        generated = read(stage / 'exchange/manifest.json')
        for arm in generated['arms']:
            for step in arm['steps']:
                if step['net'] != arm['target']:
                    continue
                target = configs[arm['name']]['task']
                order = sorted(tasks[step['net']], key=lambda task: (task != target, -criticality[task], task))
                expected = [target] + list(reversed([t for t in order if t != target]))
                actual = (step['failed_attempts'][0]['order'] if step['failed_attempts']
                          else [v['task'] for v in step['searches']])
                assert actual == expected[:len(actual)]
                if arm.get('candidate_tree') and not step['failed_attempts']:
                    assert actual == expected
                checks['target_orders'] += 1
        queue = stage / 'exchange/native_queue/protocol.json'
        if queue.exists():
            native_cases = read(queue)['cases']
            assert len(record['candidate_audits']) == len(native_cases)
            assert {v['net'] for v in native_cases} == {Path(v).parent.name for v in record['candidate_audits']}
            checks['all_unique_candidate_audits_present'] += 1
        for name in record.get('candidate_audits', []):
            audit = read(name)
            tree = Path(name).parent / 'candidate/route.route_trees.csv'
            nets = collections.defaultdict(set)
            with tree.open() as stream:
                for row in csv.DictReader(stream):
                    nets[int(row['net_id'])].update(int(row[k]) for k in ['source', 'parent', 'child'])
            assert sum(weights[v] for nodes in nets.values() for v in nodes) == audit['wirelength']
            refs[str(tree)] = hashlib.sha256(tree.read_bytes()).hexdigest()
            checks['native_wirelengths'] += 1
    chain = read(directory / 'independent_audit.json')
    read(directory / 'policy_audit.json')
    if mode == 'wirelength':
        read(directory / 'wirelength_audit.json')
    for name in tools:
        path = root / 'tools' / name
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in [directory / 'protocol.json', directory / 'manifest.json', Path(__file__).resolve()]:
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {'status': 'prospective_native_mode_acceptance_orders_and_native_wirelength_reviewed',
              'label': protocol['prospective_label'], 'mode': mode, 'checks': checks,
              'final_original_baseline_joint_pass': chain['final_original_baseline_joint_pass'],
              'current_state': manifest['current_state'], 'source_sha256': refs,
              'scope': 'Recorded ranked selection/native acceptance, first target orders and every unique native candidate wirelength. Per-net incremental charge proof additionally applies only to wirelength mode. Not optimal-search proof, independent full execution repeat or board result.',
              'research_complete': False}
    with (directory / 'mode_audit.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'mode': mode, 'checks': checks}))


if __name__ == '__main__':
    main()
