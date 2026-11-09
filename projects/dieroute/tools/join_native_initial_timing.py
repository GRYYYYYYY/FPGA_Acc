"""Bind observed native initial timing to logical pins and prepare a Task-only ablation."""
import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path

TASK = struct.Struct('<IIIIHHIII')
KEY = ('net_id', 'net_pin_index')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def checked_proof(path, status):
    proof = json.loads(path.read_text())
    assert proof['status'] == status, (path, proof['status'])
    assert proof['source_sha256'], path
    for name, expected in proof['source_sha256'].items():
        assert sha(name) == expected, ('changed evidence', name)
    return proof


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def join_rows(mapping, observed, task_bytes):
    """Keep logical identity, exact endpoint identity, and all non-q Task bytes."""
    packed = list(TASK.iter_unpack(task_bytes))
    by_pin = {}
    for row in observed:
        key = tuple(int(row[k]) for k in KEY)
        assert key not in by_pin, ('duplicate native pin', key)
        by_pin[key] = row
    map_keys = [tuple(int(row[k]) for k in KEY) for row in mapping]
    assert len(set(map_keys)) == len(mapping), 'duplicate mapped pin'
    assert set(map_keys) == set(by_pin), 'native/mapped logical pin set mismatch'
    assert len(packed) == len(mapping), 'task count mismatch'
    joined = []
    output = bytearray()
    for index, (identity, task) in enumerate(zip(mapping, packed)):
        assert tuple(int(identity[k]) for k in ('task_id', 'net_id', 'source_rr', 'sink_rr')) == task[:4]
        assert task[0] == index
        native = by_pin[tuple(int(identity[k]) for k in KEY)]
        assert (int(native['source_rr']), int(native['sink_rr'])) == task[2:4], 'native endpoint mismatch'
        delay, raw, route_q, cap, exponent = [float(native[k]) for k in
            ('lookahead_delay_s', 'policy_input_criticality', 'route_criticality', 'max_criticality', 'criticality_exp')]
        assert all(math.isfinite(x) for x in (delay, raw, route_q, cap, exponent))
        assert delay >= 0 and 0 <= raw <= 1 and 0 <= route_q <= cap <= 1
        assert int(native['is_clock']) in (0, 1) and exponent == 1
        # Reproduce the observed exponent-one float32 policy before quantization.
        shifted = struct.unpack('<f', struct.pack('<f', max(raw - (1.0 - cap), 0.0)))[0]
        assert route_q == min(shifted, cap), 'native criticality policy mismatch'
        # Explicit nearest-integer, ties-to-even; not native float arithmetic equivalence.
        quantized = round(route_q * 65535)
        assert 0 <= quantized <= 64880
        candidate = list(task)
        candidate[4] = quantized
        output.extend(TASK.pack(*candidate))
        joined.append(dict(identity, **{k: v for k, v in native.items() if k not in identity},
                           original_criticality_q=task[4], initial_criticality_q=quantized))
    # Byte-level independence from the tuple comparison above: q is offset 16..17.
    assert len(output) == len(task_bytes)
    for offset in range(0, len(output), TASK.size):
        assert output[offset:offset + 16] == task_bytes[offset:offset + 16]
        assert output[offset + 18:offset + TASK.size] == task_bytes[offset + 18:offset + TASK.size]
    return joined, bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('pin_mapping', type=Path)
    parser.add_argument('pair', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build, pin, pair, output = [p.resolve() for p in (args.build, args.pin_mapping, args.pair, args.output)]
    assert not output.exists(), output
    observation_path = build / 'initial_observation_audit.json'
    native_path = build / 'native_compatibility_audit.json'
    pin_path = pin / 'audit.json'
    observation = checked_proof(observation_path,
        'five_native_canonical_compatible_initial_timing_observations_identical_and_policy_checked')
    native = checked_proof(native_path, 'five_repeat_source_bound_vpr_native_baseline_compatibility_audited')
    pins = checked_proof(pin_path, 'original_route_logical_sink_pin_order_matches_connections_and_packed_tasks')
    assert native['numerical_and_canonical_compatibility'] and len(native['cases']) == 5
    original = json.loads(pair.read_text())
    case = Path(original['case'])
    assert pins['source_sha256'][str(pair)] == sha(pair)
    assert native['source_sha256'][str(case / 'run.json')] == sha(case / 'run.json')
    for name, expected in native['historical_canonical_sha256'].items():
        assert sha(case / name) == expected, ('historical identity mismatch', name)
    assert observation['source_sha256'][str(native_path)] == sha(native_path)
    task_path = pair.parent / 'input.tasks'
    map_path = pin / 'task_pin_identity.csv'
    assert pins['source_sha256'][str(task_path)] == sha(task_path)
    assert pins['source_sha256'][str(map_path)] == sha(map_path)
    csvs = [build / f'initial_timing_{i}.csv' for i in range(5)]
    assert len({sha(path) for path in csvs}) == 1
    for path in csvs:
        assert observation['source_sha256'][str(path)] == sha(path)
    joined, new_tasks = join_rows(read_csv(map_path), read_csv(csvs[0]), task_path.read_bytes())
    assert len(joined) == pins['tasks'] == observation['rows']
    output.mkdir()
    matched = output / 'initial_timing_by_task.csv'
    with matched.open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(joined[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(joined)
    candidate = output / 'native_initial.tasks'
    candidate.write_bytes(new_tasks)
    values = [r['initial_criticality_q'] for r in joined]
    source_files = [Path(__file__).resolve(), observation_path, native_path, pin_path, pair,
                    map_path, task_path, *csvs, case / 'run.json',
                    *[case / name for name in native['historical_canonical_sha256']]]
    proof = dict(status='native_initial_timing_joined_by_logical_pin_and_task_only_candidate_prepared',
        tasks=len(joined), identical_native_repetitions=5,
        exact_logical_pin_and_endpoint_sets=True, noncriticality_task_bytes_unchanged=True,
        initial_q_min=min(values), initial_q_max=max(values), initial_q_distinct=len(set(values)),
        changed_tasks=sum(r['original_criticality_q'] != r['initial_criticality_q'] for r in joined),
        zero_observed_lookahead_delays=sum(float(r['lookahead_delay_s']) == 0 for r in joined),
        quantization='round(route_criticality * 65535), nearest integer with ties to even',
        source_sha256={str(p): sha(p) for p in source_files},
        output_sha256={str(p): sha(p) for p in [matched, candidate]},
        scope='Ex5p historical canonical identity, five native observations, and exact logical pin/task join. '
              'Candidate replaces only initial Task criticality; later STA policy unchanged. '
              'Quantized observation, not all-input native equivalence, QoR acceptance or adoption.',
        adopted=False, board_result=False, research_complete=False)
    (output / 'audit.json').write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({k: v for k, v in proof.items() if k not in ('source_sha256', 'output_sha256', 'scope')}))


if __name__ == '__main__':
    main()
