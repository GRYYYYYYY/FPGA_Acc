"""Freeze capacity-aware baseline restorations for observed critical regressions."""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import mmap
import struct
from capacity_restore_closure import restore_closure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--maximum-tasks', type=int, default=2)
    args = parser.parse_args()
    root = args.experiment.resolve()
    state = json.loads((root / 'manifest.json').read_text())
    assert state['status'] == 'experiment_terminal_all_selected_tasks_exhausted'
    assert args.maximum_tasks > 0
    current = state['current_state']
    protocol = json.loads((root / 'stage_001/exchange/protocol.json').read_text())
    observation = root / ('stage_' + str(state['active_stage']).zfill(3)) / 'observation'
    selected = json.loads((observation / 'selection.json').read_text())['selected'][:args.maximum_tasks]
    assert selected
    protocol.update(candidate_tree=current['tree'],
                    native_parent_observations=str(observation / 'parent/native_observations.csv'))

    def load(path):
        nets = collections.defaultdict(list)
        with Path(path).open() as stream:
            for row in csv.DictReader(stream):
                nets[int(row['net_id'])].append(row)
        return nets

    def allocations(nets):
        return {n: {int(row[k]) for row in rows for k in ['source', 'parent', 'child']}
                for n, rows in nets.items()}

    with Path(protocol['connections']).open() as stream:
        tasks = {int(row['id']): int(row['net_id']) for row in csv.DictReader(stream)}
    baseline = load(protocol['baseline_tree'])
    candidate = load(current['tree'])
    ba, ca = allocations(baseline), allocations(candidate)
    used = set().union(*ba.values(), *ca.values())
    with Path(protocol['resources']).open('rb') as stream:
        capacities = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
        caps = {node: struct.unpack_from('<H', capacities, 16 * node + 2)[0] for node in used}
        capacities.close()
    ids = [v['task'] for v in selected]
    plans = [('task' + str(task), [task]) for task in ids]
    if len(ids) > 1:
        plans.append(('all_selected', ids))
    args.output.mkdir()
    arms, configs, construction = [], [], []
    for name, task_ids in plans:
        seeds = {tasks[t] for t in task_ids}
        restored, waves = restore_closure(ba, ca, caps, seeds)
        folder = args.output / name
        folder.mkdir()
        tree = folder / 'candidate.route_trees.csv'
        with tree.open('x') as stream:
            writer = csv.DictWriter(stream, fieldnames=['net_id', 'source', 'parent', 'child'], extrasaction='ignore')
            writer.writeheader()
            for net in sorted(candidate):
                rows = baseline[net] if net in restored else candidate[net]
                writer.writerows(sorted(rows, key=lambda row: (int(row['child']), int(row['parent']))))
        arms.append({'name': name, 'candidate_tree': str(tree.resolve()),
                     'candidate_tree_sha256': hashlib.sha256(tree.read_bytes()).hexdigest(),
                     'status': 'capacity_closure_complete_requires_native_validation'})
        configs.append({'name': name, 'task': task_ids[0],
                        'order': sorted(restored - {tasks[task_ids[0]]})})
        construction.append({'name': name, 'seed_tasks': task_ids, 'seed_nets': sorted(seeds),
                             'restored_nets': sorted(restored), 'waves': waves})
    files = [Path(protocol[k]) for k in ['baseline_tree', 'candidate_tree', 'connections', 'resources', 'node_die']]
    files.extend([observation / 'selection.json', root / 'independent_audit.json',
                  Path(__file__).resolve(), Path(__file__).resolve().with_name('capacity_restore_closure.py')])
    protocol['source_sha256'].update({str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
    protocol.update(arms=configs, scope='Posterior fixed first-ranked critical tasks individually and together; actual-capacity whole-net restoration closure. Extra baseline switch_id column is omitted from common four-field tree ABI; native writer and validator must prove edge legality. Not minimality, generalization or performance.')
    for name, value in [('protocol.json', protocol),
                        ('manifest.json', {'status': 'budgeted_exchange_arms_terminal_require_review', 'arms': arms, 'research_complete': False}),
                        ('closure_construction.json', {'closures': construction, 'maximum_tasks': args.maximum_tasks, 'research_complete': False})]:
        (args.output / name).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps([{'name': v['name'], 'restored_nets': len(v['restored_nets'])} for v in construction]))


if __name__ == '__main__':
    main()
