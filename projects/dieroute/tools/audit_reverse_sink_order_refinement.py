"""Check recorded first sink orders against the frozen reversal rule."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import sys


def main():
    directory = Path(sys.argv[1]).resolve()
    refs = {}

    def read(path):
        path = Path(path)
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    manifest = read(directory / 'manifest.json')
    assert manifest['status'].startswith('experiment_terminal_')
    assert read(directory / 'independent_audit.json')['status'] == 'private_refinement_monotone_native_acceptance_and_stop_reviewed'
    assert read(directory / 'policy_audit.json')['status'] == 'rounded_budgets_blocker_first_order_and_native_decisions_verified'
    assert read(directory / 'wirelength_audit.json')['status'] == 'incremental_wire_charges_and_native_totals_verified'
    checked = []
    for record in manifest['stages']:
        exchange = directory / ('stage_' + str(record['iteration']).zfill(3)) / 'exchange'
        if not (exchange / 'protocol.json').exists():
            continue
        protocol = read(exchange / 'protocol.json')
        assert protocol['reverse_target_remaining_sinks'] is True
        tasks = collections.defaultdict(list)
        with Path(protocol['connections']).open() as stream:
            for row in csv.DictReader(stream):
                tasks[int(row['net_id'])].append(int(row['id']))
        with Path(protocol['native_parent_observations']).open() as stream:
            criticality = {int(row['task_id']): int(row['criticality_q']) for row in csv.DictReader(stream)}
        arms = {v['name']: v for v in protocol['arms']}
        generated = read(exchange / 'manifest.json')
        for arm in generated['arms']:
            for step in arm['steps']:
                if step['net'] != arm['target']:
                    continue
                target = arms[arm['name']]['task']
                original = sorted(tasks[step['net']], key=lambda task: (task != target, -criticality[task], task))
                expected = [target] + list(reversed([t for t in original if t != target]))
                actual = (step['failed_attempts'][0]['order'] if step['failed_attempts']
                          else [v['task'] for v in step['searches']])
                assert actual == expected[:len(actual)], (arm['name'], actual, expected)
                if not step['failed_attempts'] and arm.get('candidate_tree'):
                    assert actual == expected
                checked.append({'stage': record['iteration'], 'arm': arm['name'],
                                'target_task': target, 'initial_sink_count_checked': len(actual)})
    refs[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = {'status': 'recorded_target_sink_reversal_rule_verified', 'orders': checked,
              'source_sha256': refs, 'research_complete': False,
              'scope': 'Recorded first target-net order only; failed-sink rollback orders may differ by protocol. No quality generalization or board claim.'}
    with (directory / 'sink_order_audit.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'orders': len(checked)}))


if __name__ == '__main__':
    main()
