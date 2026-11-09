"""Compare native regression input hashes with the frozen reference reports.

This supplements trajectory/feedback/placement audits; it cannot replace them.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def input_map(records):
    result = {}
    for record in records:
        path = str(Path(record['path']).resolve())
        if path in result:
            raise ValueError(f'duplicate input record: {path}')
        result[path] = record['sha256']
    return result


def compare_inputs(actual, expected):
    left, right = input_map(actual), input_map(expected)
    if left != right:
        raise ValueError({'missing': sorted(right.keys() - left.keys()),
                          'extra': sorted(left.keys() - right.keys()),
                          'changed': sorted(name for name in left.keys() & right.keys()
                                            if left[name] != right[name])})
    return len(right)


def audit(manifest_path, allow_incomplete=False):
    manifest = json.loads(manifest_path.read_text())
    expected_files = {}
    matched = []
    pending = []
    references = []
    for case in manifest['cases']:
        reference_path = Path(case['reference'])
        if digest(reference_path) != case['reference_sha256']:
            raise ValueError(f'reference report changed: {reference_path}')
        reference = json.loads(reference_path.read_text())
        expected = reference['provenance']['inputs']
        for path, value in input_map(expected).items():
            if path in expected_files and expected_files[path] != value:
                raise ValueError(f'inconsistent frozen input: {path}')
            expected_files[path] = value
        references.append({'case': case['case'], 'path': str(reference_path),
                           'sha256': case['reference_sha256'], 'input_count': len(expected)})
        run = Path(case['run'])
        # The batch writes process.json only after the native command exits.
        if not (run / 'process.json').exists():
            pending.append(case['case'])
            continue
        process = json.loads((run / 'process.json').read_text())
        if process['returncode'] != 0:
            raise ValueError(f'native case failed: {case["case"]}')
        report_path = run / 'report.json'
        report = json.loads(report_path.read_text())
        if report['status'] != 'pass':
            raise ValueError(f'native report failed: {case["case"]}')
        count = compare_inputs(report['provenance']['inputs'], expected)
        matched.append({'case': case['case'], 'inputs': count,
                        'report': str(report_path), 'report_sha256': digest(report_path)})
    for path, expected in expected_files.items():
        if digest(Path(path)) != expected:
            raise ValueError(f'frozen input changed: {path}')
    if pending and not allow_incomplete:
        raise ValueError(f'native cases incomplete: {pending}')
    return {'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'status': 'pass' if not pending else 'partial',
            'scope': 'exact native/reference input identity plus current frozen-file integrity; '
                     'not trajectory, RTL, timing or board evidence',
            'planned_cases': len(manifest['cases']), 'matched_cases': matched,
            'pending_cases': pending, 'unique_frozen_inputs_verified': len(expected_files),
            'all_completed_input_maps_equal': bool(matched),
            'all_expected_input_maps_equal': not pending and bool(matched),
            'references': references, 'manifest_sha256': digest(manifest_path),
            'auditor_sha256': digest(Path(__file__))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    result = audit(args.manifest, args.allow_incomplete)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
                     ['status', 'planned_cases', 'unique_frozen_inputs_verified',
                      'pending_cases', 'all_expected_input_maps_equal']}))
