"""Verify terminal encoded-transfer receipts and referenced replay evidence."""
import csv
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = root/'work/rr_task_transfer_variant_20261015'
sources = {}

def read(f):
    raw = f.read_bytes()
    sources[str(f)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)

queue = read(p/'postrun_audit_queue/manifest.json')
assert queue['status'] == 'all_fifteen_encoded_native_runs_replayed_and_parent_matched'
expected = [f'mode{m}_{i}' for m in range(3) for i in range(5)]
assert queue['audited'] == expected
verified = {}
runs = []

def verify_refs(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == 'source_sha256':
                for name, expected_hash in v.items():
                    f = Path(name)
                    if name not in verified:
                        h = hashlib.sha256()
                        with f.open('rb') as stream:
                            for block in iter(lambda: stream.read(1048576), b''):
                                h.update(block)
                        verified[name] = h.hexdigest()
                    assert verified[name] == expected_hash, name
            else:
                verify_refs(v)
    elif isinstance(x, list):
        for v in x:
            verify_refs(v)

for label in expected:
    d = p/'native_runs_v2'/label
    receipt = read(d/'placement_trace_audit.json')
    resources = read(d/'controller_resource_replay_audit.json')
    tree = read(d/'final_tree_state_audit.json')
    parent = read(d/'matched_static_parent_audit.json')
    assert receipt['status'] == 'static_task_placement_receipts_bound_to_tasks_and_ordered_transactions'
    assert resources['status'] == 'encoded_transfer_controller_versions_and_final_bytes_replayed'
    assert resources['result']['final_resources_and_costs_byte_equivalent']
    assert tree['status'] == 'final_native_rr_tree_connectivity_and_resource_memberships_reconstructed'
    assert parent['status'] == 'encoded_transfer_native_run_matches_static_parent'
    original = root/'work/rr_task_migration_variant_20261015/native_runs_v2'/label
    for c in parent['checks']:
        a, b = original/c['name'], d/c['name']
        verify_refs({'source_sha256': {str(a):c['parent_sha256'], str(b):c['encoded_sha256']}})
        if c['name'] == 'route.json':
            left, right = json.loads(a.read_text()), json.loads(b.read_text())
            left.pop('wall_ms'); right.pop('wall_ms')
            assert left == right
        elif c['name'] == 'route.task_migration.csv':
            with a.open() as stream: left = list(csv.DictReader(stream))
            with b.open() as stream: right = list(csv.DictReader(stream))
            for row in left: row.pop('logical_envelope_bytes')
            for row in right: row.pop('encoded_envelope_bytes')
            assert left == right
        else:
            assert c['parent_sha256'] == c['encoded_sha256']
    for x in [receipt, resources, tree]:
        verify_refs(x)
    runs.append(dict(label=label, receipts=receipt['receipts'],
                     encoded_bytes=receipt['encoded_all_envelope_bytes'],
                     moved_encoded_bytes=receipt['encoded_moved_envelope_bytes'],
                     matched_parent_artifacts=len(parent['checks'])))
quality = {}
for mode in range(3):
    q = read(p/f'native_runs_v2/mode{mode}_0/native_validation/validation.json')
    assert q['legal'] and q['vpr_exit_status'] == 0
    quality[str(mode)] = dict(wirelength=q['total_wirelength'], cpd_ns=q['critical_path_delay_ns'],
                             joint_quality_pass=q['total_wirelength'] <= q['baseline_wirelength'] and q['critical_path_delay_ns'] <= q['baseline_cpd_ns'])
result = dict(status='fifteen_encoded_transfer_replay_receipts_and_referenced_hashes_verified',
              runs=runs, quality=quality, verified_referenced_files=len(verified),
              source_sha256=sources,
              scope='Terminal replay receipts and referenced file integrity. One native validation per mode; five repeats matched via producer parent-artifact receipts. Does not rerun search or prove physical transport, throughput or energy.',
              board_result=False, research_complete=False)
with (p/'terminal_evidence_review.json').open('x') as out:
    json.dump(result,out,indent=2)
    out.write('\n')
print(json.dumps(dict(status=result['status'],verified_referenced_files=len(verified),quality=quality)))
