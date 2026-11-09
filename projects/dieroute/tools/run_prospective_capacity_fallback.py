"""Apply the preregistered first-two-critical-task capacity closure fallback."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import mmap
import struct
import subprocess
import sys
import time
from capacity_restore_closure import restore_closure


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    mode = args.mode.resolve()
    output = args.output.resolve()
    mp = json.loads((mode / 'protocol.json').read_text())
    state = json.loads((mode / 'manifest.json').read_text())
    audited = json.loads((mode / 'mode_audit.json').read_text())
    assert mp['prospective_mode'] == 'delay'
    assert audited['status'] == 'prospective_native_mode_acceptance_orders_and_native_wirelength_reviewed'
    assert audited['current_state'] == state['current_state'] and not audited['final_original_baseline_joint_pass']
    assert state['status'] in ['experiment_terminal_all_selected_tasks_exhausted',
                               'experiment_terminal_frozen_stage_budget_exhausted', 'experiment_terminal_no_selected_regression']
    output.mkdir()
    started = time.monotonic_ns()
    refs = {}

    def sha(path):
        path = Path(path).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        refs[str(path)] = digest
        return digest

    def bind(paths):
        return {str(Path(p).resolve()): sha(p) for p in paths}

    def write(path, value):
        with Path(path).open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')

    def run(command, name):
        with (output / (name + '.log')).open('x') as stream:
            subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, check=True)

    for path, expected in audited['source_sha256'].items():
        assert sha(path) == expected, path
    current = state['current_state']
    observation = output / 'observation'
    observation.mkdir()
    (observation / 'parent').mkdir()
    op = json.loads(Path(mp['observation_template']).read_text())
    case = next(c for c in op['cases'] if c['name'] == 'parent')
    cmd = case['command']
    cmd[cmd.index('--route') + 1] = current['route']
    cmd[cmd.index('--work-dir') + 1] = str(observation / 'parent/native_validation')
    case['environment']['PERSISTROUTE_VPR_TIMING_OUTPUT'] = str(observation / 'parent/native_observations.csv')
    op['cases'] = [case]
    op['parent_tree'] = current['tree']
    files = [Path(v) for v in cmd if Path(v).is_file()]
    files.extend([Path(case['environment']['PERSISTROUTE_VPR_TIMING_INPUT']), Path(current['tree']), Path(op['connections'])])
    op['source_sha256'] = bind(files)
    write(observation / 'protocol.json', op)
    for tool in ['run_native_RC_observations.py', 'audit_native_RC_observations.py']:
        run(['python3', str(root / 'tools' / tool), str(observation)], tool)
    refreshed = json.loads((observation / 'parent/native_validation/validation.json').read_text())
    assert refreshed['legal'] and (refreshed['total_wirelength'], refreshed['critical_path_delay_ns']) == (current['wirelength'], current['cpd_ns'])
    selection = observation / 'selection.json'
    run(['python3', str(root / 'tools/select_regressed_critical_connections.py'), mp['baseline_observations'],
         str(observation / 'parent/native_observations.csv'), str(selection)], 'selection')
    selected = json.loads(selection.read_text())['selected'][:2]
    common = [mode / 'protocol.json', mode / 'manifest.json', mode / 'mode_audit.json', selection,
              observation / 'independent_audit.json', Path(__file__).resolve(), root / 'tools/capacity_restore_closure.py']
    for path in common:
        sha(path)
    if not selected:
        write(output / 'fallback_result.json', {'status': 'capacity_fallback_no_regressed_critical_targets',
              'label': mp['prospective_label'], 'joint_quality_pass': False, 'current_state': current,
              'source_sha256': refs, 'research_complete': False})
        return
    ep = json.loads(Path(mp['exchange_template']).read_text())
    ep.update(candidate_tree=current['tree'], native_parent_observations=str(observation / 'parent/native_observations.csv'))

    def load(path):
        nets = collections.defaultdict(list)
        with Path(path).open() as stream:
            for row in csv.DictReader(stream):
                nets[int(row['net_id'])].append(row)
        return nets

    def allocation(nets):
        return {net: {int(row[k]) for row in rows for k in ['source', 'parent', 'child']} for net, rows in nets.items()}

    baseline = load(ep['baseline_tree'])
    candidate = load(current['tree'])
    ba, ca = allocation(baseline), allocation(candidate)
    with Path(ep['connections']).open() as stream:
        tasks = {int(row['id']): int(row['net_id']) for row in csv.DictReader(stream)}
    used = set().union(*ba.values(), *ca.values())
    with Path(ep['resources']).open('rb') as stream:
        resources = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
        capacities = {node: struct.unpack_from('<H', resources, 16 * node + 2)[0] for node in used}
        resources.close()
    ids = [v['task'] for v in selected]
    plans = [('task' + str(task), [task]) for task in ids]
    if len(ids) == 2:
        plans.append(('all_selected', ids))
    arms, configs, constructions = [], [], []
    for name, task_ids in plans:
        restored, waves = restore_closure(ba, ca, capacities, {tasks[t] for t in task_ids})
        folder = output / name
        folder.mkdir()
        tree = folder / 'candidate.route_trees.csv'
        with tree.open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=['net_id', 'source', 'parent', 'child'], extrasaction='ignore')
            writer.writeheader()
            for net in sorted(candidate):
                rows = baseline[net] if net in restored else candidate[net]
                writer.writerows(sorted(rows, key=lambda row: (int(row['child']), int(row['parent']))))
        arms.append({'name': name, 'candidate_tree': str(tree), 'candidate_tree_sha256': sha(tree),
                     'status': 'capacity_closure_complete_requires_native_validation'})
        configs.append({'name': name, 'task': task_ids[0], 'order': sorted(restored - {tasks[task_ids[0]]})})
        constructions.append({'name': name, 'seed_tasks': task_ids, 'restored_nets': sorted(restored), 'waves': waves})
    ep.update(arms=configs, generation_kind='preregistered_capacity_closure',
              scope='Fixed first2 ranked current regressed critical tasks individually and together; exact capacity closure. No manual target or full-baseline substitution.')
    files = common + [Path(ep[k]) for k in ['candidate_tree', 'baseline_tree', 'connections', 'resources', 'node_die']]
    ep['source_sha256'].update(bind(files))
    write(output / 'protocol.json', ep)
    write(output / 'manifest.json', {'status': 'budgeted_exchange_arms_terminal_require_review', 'arms': arms, 'research_complete': False})
    write(output / 'closure_construction.json', {'closures': constructions, 'total_nets': len(baseline), 'research_complete': False})
    if not args.run:
        return
    run(['python3', str(root / 'tools/prepare_native_exchange_validation.py'), str(output), mp['native_template']], 'native_prepare')
    queue = output / 'native_queue'
    receipt = json.loads((queue / 'launch_receipt.json').read_text())
    while True:
        try:
            native_state = json.loads((queue / 'manifest.json').read_text())
        except (OSError, json.JSONDecodeError):
            native_state = {}
        if native_state.get('status') == 'all_native_candidates_terminal_require_independent_review':
            break
        assert native_state.get('status') != 'candidate_supervision_failed_requires_review', native_state
        process = Path('/proc') / str(receipt['pid']) / 'cmdline'
        if not process.exists() or str(queue / 'supervise.py').encode() not in process.read_bytes():
            # Re-read the terminal receipt after process exit; observation is not a restart trigger.
            try:
                final_state = json.loads((queue / 'manifest.json').read_text())
            except (OSError, json.JSONDecodeError):
                final_state = {}
            if final_state.get('status') == 'all_native_candidates_terminal_require_independent_review':
                break
            raise RuntimeError('Original native owner missing without terminal receipt; reconcile without replay')
        time.sleep(3)
    eligible = []
    outcomes = []
    for case in json.loads((queue / 'protocol.json').read_text())['cases']:
        arm = case['net']
        run(['python3', str(root / 'tools/audit_protocol_budgeted_exchange_native_v3.py'), str(output), arm], 'audit_' + arm)
        path = queue / arm / 'independent_native_audit.json'
        audit = json.loads(path.read_text())
        sha(path)
        outcomes.append({'arm': arm, 'audit': str(path), 'checks': audit['checks']})
        if all(audit['checks'].values()):
            eligible.append((audit['cpd_ns'], audit['wirelength'], audit['model_crossings'], arm))
    chosen = min(eligible)[3] if eligible else None
    for path in [output / 'protocol.json', output / 'manifest.json', output / 'closure_construction.json', queue / 'protocol.json']:
        sha(path)
    write(output / 'fallback_result.json', {'status': 'preregistered_capacity_fallback_terminal_reviewed',
          'label': mp['prospective_label'], 'outcomes': outcomes, 'joint_quality_pass': chosen is not None,
          'selected_arm': chosen, 'previous_state': current, 'generated_arms': len(arms),
          'unique_native_candidates': len(outcomes), 'wall_ns': time.monotonic_ns() - started,
          'source_sha256': refs, 'scope': 'Fixed baseline-guided fallback only. Restoration extent and all outcomes retained. No independent circuit generalization, statistical significance or board performance.',
          'research_complete': False})
    print(json.dumps({'label': mp['prospective_label'], 'joint_quality_pass': chosen is not None, 'unique_candidates': len(outcomes)}))


if __name__ == '__main__':
    main()
