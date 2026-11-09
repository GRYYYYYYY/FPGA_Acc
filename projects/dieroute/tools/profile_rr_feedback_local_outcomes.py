"""Describe local delays across executed supplemental reroutes, without causal claims."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    parser.add_argument('pair', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    profile = json.loads(args.profile.read_text())
    assert profile['status'] == 'observed_supplemental_feedback_delay_changes_profiled'
    for path, digest in profile['source_sha256'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    pair = args.pair.resolve()
    assert str(pair) in profile['source_sha256']
    files = [Path(__file__).resolve(), args.profile.resolve(), pair]
    modes = {}
    for mode, data in profile['modes'].items():
        cache = {}

        def inputs(iteration):
            if iteration not in cache:
                path = pair.parent / f'{mode}_0.timing_iteration_{iteration}.input.csv'
                files.append(path)
                with path.open() as stream:
                    cache[iteration] = {int(row['task_id']): {k: int(v) for k, v in row.items()}
                                        for row in csv.DictReader(stream)}
            return cache[iteration]

        events = []
        for event in data['events']:
            iteration = event['iteration']
            before, after = inputs(iteration), inputs(iteration + 1)
            crossing = {row['task_id'] for row in event['crossed_connections']}
            tasks = [task for task, row in before.items() if row['net_id'] == event['net_id']]
            changes = []
            for task in tasks:
                old, new = before[task], after[task]
                assert old['routed'] == new['routed'] == 1
                changes.append(dict(task_id=task, crossed_cap=task in crossing,
                                    before_ps=old['delay_ps'], after_ps=new['delay_ps'],
                                    delta_ps=new['delay_ps'] - old['delay_ps']))
            selected = [row['delta_ps'] for row in changes if row['crossed_cap']]
            assert selected
            outcome = ('mixed' if min(selected) < 0 < max(selected) else
                       'slower' if max(selected) > 0 else
                       'faster' if min(selected) < 0 else 'unchanged')
            events.append(dict(iteration=iteration, net_id=event['net_id'],
                               trigger_category=event['category'], crossing_outcome=outcome,
                               connections=changes))
        modes[mode] = dict(events=events, event_count=len(events),
                           crossing_outcomes=dict(Counter(e['crossing_outcome'] for e in events)),
                           by_trigger={category: dict(Counter(e['crossing_outcome'] for e in events
                                                             if e['trigger_category'] == category))
                                       for category in sorted({e['trigger_category'] for e in events})})
    report = dict(status='executed_supplemental_local_delay_outcomes_profiled', modes=modes,
                  source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  scope='Iteration i to i+1 STA-input path delays on the executed trajectory only. '
                        'All connections of each supplemental net are retained. Other nets reroute concurrently '
                        'within this serial epoch, changing congestion and global STA. No counterfactual '
                        'benefit, causal CPD attribution, native timing bound or proposed-filter validation.',
                  research_complete=False, board_result=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({mode: {k: v for k, v in data.items() if k != 'events'}
                      for mode, data in modes.items()}))


if __name__ == '__main__':
    main()
