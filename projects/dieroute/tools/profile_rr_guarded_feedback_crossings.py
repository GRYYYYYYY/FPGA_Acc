"""Describe cap crossings on the audited guarded trajectory, not counterfactual savings."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair', type=Path)
    parser.add_argument('audit', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    pair, audit = args.pair.resolve(), args.audit.resolve()
    proof = json.loads(audit.read_text())
    assert proof['status'] == 'five_repeat_critical_feedback_pending_and_owner_replay_audited'
    for path, digest in proof['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    assert proof['source_sha256'][str(pair)] == hashlib.sha256(pair.read_bytes()).hexdigest()
    manifest = json.loads(pair.read_text())
    assert manifest['configuration']['feedback_local_delay_guard'] is True
    threshold = manifest['configuration']['criticality_feedback_threshold_q']
    assert threshold > 0
    files = [Path(__file__).resolve(), pair, audit]

    def rows(path):
        files.append(path)
        with path.open() as stream:
            return [{k: int(v) for k, v in row.items()} for row in csv.DictReader(stream)]

    modes = {}
    for mode, result in proof['modes'].items():
        assert result['local_delay_guard'] is True
        prefix = pair.parent / (mode + '_0')
        trace = rows(Path(str(prefix) + '.critical_feedback.csv'))
        feedback = {(r['iteration'], r['net_id']): r for r in trace}
        assert len(feedback) == len(trace)
        previous = None
        crossings = []
        eligible = defaultdict(list)
        for iteration in range(result['iterations']):
            current = {r['task_id']: r for r in rows(Path(str(prefix) + f'.timing_iteration_{iteration}.input.csv'))}
            output = {r['task_id']: r for r in rows(Path(str(prefix) + f'.timing_iteration_{iteration}.output.csv'))}
            for task, row in current.items():
                if not row['criticality_q'] < threshold <= output[task]['criticality_q']:
                    continue
                before = previous[task] if previous is not None else None
                delta = row['delay_ps'] - before['delay_ps'] if before else None
                category = ('missing_history' if before is None else
                            'not_routed_in_both' if before['routed'] != 1 or row['routed'] != 1 else
                            'local_delay_not_increased' if delta <= 0 else 'eligible')
                event = dict(iteration=iteration, net_id=row['net_id'], task_id=task,
                             old_q=row['criticality_q'], new_q=min(threshold, output[task]['criticality_q']),
                             category=category, delta_ps=delta)
                crossings.append(event)
                if category == 'eligible':
                    eligible[iteration, row['net_id']].append(task)
            previous = current
        assert set(eligible) == set(feedback)
        for key, tasks in eligible.items():
            assert feedback[key]['task_id'] == min(tasks)
        decisions = Counter(row['decision'] for row in trace)
        assert decisions[1] == result['supplemental_events']
        modes[mode] = dict(cap_crossing_connections=len(crossings),
                           crossing_categories=dict(Counter(r['category'] for r in crossings)),
                           eligible_net_epoch_events=len(eligible), feedback_decisions=dict(decisions),
                           actual_supplemental_events=decisions[1], crossings=crossings)
    report = dict(status='audited_guarded_trajectory_crossings_profiled', modes=modes,
                  source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                  scope='Counts on this executed guarded trajectory only. A rejected connection crossing '
                        'does not imply a rejected net event if another connection qualifies. Ordinary '
                        'pending, prior allowance and budget determine actual scheduling. No direct '
                        'counterfactual savings, global-CPD attribution or general filtering benefit.',
                  research_complete=False, board_result=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({mode: {k: v for k, v in data.items() if k != 'crossings'}
                      for mode, data in modes.items()}))


if __name__ == '__main__':
    main()
