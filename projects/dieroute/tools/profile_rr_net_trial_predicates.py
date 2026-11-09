"""Describe audited candidate predicates without simulating a different trajectory."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair', type=Path)
    parser.add_argument('paths', type=Path)
    parser.add_argument('versions', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    pair = args.pair.resolve()
    proof_paths = [args.paths.resolve(), args.versions.resolve()]
    proofs = [json.loads(p.read_text()) for p in proof_paths]
    expected = ['five_repeat_net_trial_paths_pending_and_predicates_audited',
                'private_and_published_versions_match_trial_epoch_and_final_checkpoints']
    for proof, status in zip(proofs, expected):
        assert proof['status'] == status
        assert proof['source_sha256'][str(pair)] == hashlib.sha256(pair.read_bytes()).hexdigest()
        for path, digest in proof['source_sha256'].items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    files = [Path(__file__).resolve(), pair, *proof_paths]
    modes = {}
    for mode, result in proofs[0]['modes'].items():
        path = pair.parent / (mode + '_0.net_trials.csv')
        files.append(path)
        with path.open() as stream:
            trials = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(stream)]
        assert len(trials) == result['net_trials']
        failed = Counter()
        eligible = 0
        for row in trials:
            predicates = {k: row[k] for k in ('complete', 'delay_ok', 'wire_ok', 'capacity_ok', 'strict')}
            failed.update(k for k, v in predicates.items() if not v)
            eligible += int(all(predicates.values()))
        modes[mode] = dict(trials=len(trials), actual_published=sum(r['accepted'] for r in trials),
                           passing_all_safeguards_on_this_trajectory=eligible,
                           failed_predicate_counts=dict(failed),
                           actual_published_step_wire_delta=sum(r['trial_wire'] - r['old_wire']
                                                                for r in trials if r['accepted']),
                           private_queries=result['private_steps'], private_expanded=result['private_expanded'],
                           trials_detail=trials)
    report = dict(status='audited_net_trial_predicates_profiled', modes=modes,
                  source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  scope='Predicates on the executed, individually audited trajectory. Overlapping failure '
                        'counts are not disjoint causes. Passing/rejecting these observed candidates '
                        'does not simulate a different policy, explain global CPD, or establish final '
                        'wirelength savings; published step deltas are intermediate changes only.',
                  board_result=False, research_complete=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({mode: {k: v for k, v in data.items() if k != 'trials_detail'}
                      for mode, data in modes.items()}))


if __name__ == '__main__':
    main()
