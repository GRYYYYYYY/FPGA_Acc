#!/usr/bin/env python3
"""Independently rehash state-view comparisons and their serial controls."""
import argparse
import json
from pathlib import Path
import shutil
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('audit requires assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('run', 'legacy-audit', 'candidate-host', 'output'):
        parser.add_argument('--'+arg, required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    manifest = json.loads((run/'manifest.json').read_text())
    legacy = json.loads(args.legacy_audit.read_text())
    assert manifest['status'] == 'passed' and manifest['inputs_unchanged']
    for path, digest in manifest['inputs'].items():
        assert sha256(path) == digest, path
    for name, digest in manifest['artifacts'].items():
        assert sha256(run/name) == digest, name
    assert sha256(args.candidate_host) == manifest['binary_sha256']['candidate'] == sha256(run/'candidate')
    assert sha256(run/'reference') == manifest['binary_sha256']['reference']
    suffixes = ('.paths.csv', '.route_trees.csv', '.iterations.csv', '.audit.csv',
                '.resources', '.costs', '.timing_iterations.csv', '.transactions.csv')
    controls = {}
    for entry in legacy['runs']:
        prefix = entry['command'][3]
        for suffix, digest in entry['hashes'].items():
            assert sha256(prefix+suffix) == digest
        summary_path = Path(prefix+'.json').resolve()
        controls[str(summary_path)] = sha256(summary_path)
    grouped = {}
    for entry in manifest['runs']:
        assert entry['returncode'] == 0
        prefix = entry['command'][3]
        assert {s: sha256(prefix+s) for s in suffixes} == entry['hashes']
        actual = json.loads(Path(prefix+'.json').read_text())
        assert actual['legal'] and not actual['board_result']
        actual.pop('wall_ms', None)
        assert actual == entry['non_wall_summary']
        grouped.setdefault((entry['case'], entry['mode']), []).append(entry)
    assert set(grouped) == {('diffeq', 'serial'), ('alu4', 'serial'), ('ex5p', 'serial'),
                            ('diffeq', 'sync1'), ('diffeq', 'sync3')}
    for entry in legacy['runs']:
        candidate, = grouped[entry['case'], 'serial']
        assert candidate['host'] == 'candidate'
        assert all(candidate['hashes'][s] == digest for s, digest in entry['hashes'].items())
        actual = json.loads(Path(entry['command'][3]+'.json').read_text());actual.pop('wall_ms', None)
        assert actual == candidate['non_wall_summary']
    for mode in ('sync1', 'sync3'):
        entries = grouped['diffeq', mode]
        reference, = [e for e in entries if e['host'] == 'reference']
        candidates = [e for e in entries if e['host'] == 'candidate']
        assert len(candidates) == 5 and {e['repeat'] for e in candidates} == set(range(5))
        for candidate in candidates:
            assert candidate['hashes'] == reference['hashes']
            assert candidate['non_wall_summary'] == reference['non_wall_summary']
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, args.output/'auditor.py')
    result = dict(schema='dieroute.rr_state_view_independent_audit.v1', passed=True,
                  producer_sha256=sha256(run/'manifest.json'), legacy_sha256=sha256(args.legacy_audit),
                  candidate_sha256=sha256(args.candidate_host), serial_control_summaries=controls,
                  serial_cases=3, speculative_modes=2, candidate_repeats_per_mode=5,
                  artifacts_per_speculative_run=8, runs_rehashed=len(manifest['runs']),
                  all_non_wall_counters_equal=True, board_result=False,
                  limit='Behavioral parity and immutable borrowed-view structure; no performance or hardware evidence')
    (args.output/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'serial_control_summaries'}))


if __name__ == '__main__':
    main()
