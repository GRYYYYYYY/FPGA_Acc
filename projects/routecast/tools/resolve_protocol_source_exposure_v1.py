"""Trace hash-bound protocol declarations in an existing frozen archive snapshot.

This is declaration provenance, never a successful model/label-use certificate.
Only protocol-to-protocol edges with exact snapshot SHA256 are traversed.
"""
import datetime
import json
import re
import resource
from collections import defaultdict, deque
from pathlib import Path

from archive_design_exposure_v3 import sha

R = Path(__file__).resolve().parents[1]
HEX = re.compile('[0-9a-f]{64}')


def references(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value['path'], value['sha256']
        for key, item in value.items():
            if isinstance(key, str) and isinstance(item, str) and HEX.fullmatch(item):
                yield key, item
            yield from references(item)
    elif isinstance(value, list):
        for item in value:
            yield from references(item)


def witnesses(edges, direct):
    """A shortest declaration chain, with deterministic traversal and no cycles."""
    reverse = defaultdict(list)
    for src, targets in edges.items():
        for dst in sorted(targets):
            reverse[dst].append(src)
    found = {n: dict(next_protocol=None, declaration_record_index=direct[n], distance=0)
             for n in sorted(direct)}
    pending = deque(sorted(direct))
    while pending:
        target = pending.popleft()
        for src in sorted(reverse[target]):
            if src in found:
                continue
            found[src] = dict(next_protocol=target,
                              declaration_record_index=found[target]['declaration_record_index'],
                              distance=found[target]['distance'] + 1)
            pending.append(src)
    return found


def main():
    # Metadata-only work; reserve a full 8-GiB audit plus 8-GiB shared margin.
    limit = 512 * 2**20
    free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 16 * 2**30 + limit, 'Metadata inventory deferred by shared memory admission'
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    source = R / 'experiments/design_exposure_inventory_v3_2026-10-15/receipt.json'
    source_hash = sha(source)
    inventory = json.loads(source.read_text())
    frozen = inventory['stable_protocol_hashes']
    assert not inventory['protocols_changed_before_finish']
    absolute = {str(R / name): name for name in frozen}
    edges = {name: set() for name in frozen}
    mismatches = []
    outside = defaultdict(int)
    for name, expected in sorted(frozen.items()):
        path = R / name
        assert path.stat().st_size <= 16 * 2**20
        assert sha(path) == expected, ('snapshot drift', name)
        data = json.loads(path.read_text())
        assert sha(path) == expected
        for raw, declared in references(data):
            if Path(raw).name != 'protocol.json':
                continue
            # Relative references have no documented base here: do not guess one.
            target = absolute.get(raw)
            if target is None:
                outside[name] += 1
            elif declared != frozen[target]:
                mismatches.append(dict(protocol=name, target=target, declared_sha256=declared,
                                       snapshot_sha256=frozen[target]))
            else:
                edges[name].add(target)
    direct = {}
    for i, row in enumerate(inventory['declared_source_records']):
        if row['identity_hash_valid'] and row['protocol'] in frozen:
            direct.setdefault(row['protocol'], i)
    found = witnesses(edges, direct)
    # Independently validate every stored hop and source record, not only reachability counts.
    for name, row in found.items():
        source_row = inventory['declared_source_records'][row['declaration_record_index']]
        if row['distance'] == 0:
            assert row['next_protocol'] is None and source_row['protocol'] == name
        else:
            nxt = row['next_protocol']
            assert nxt in edges[name] and found[nxt]['distance'] == row['distance'] - 1
            assert found[nxt]['declaration_record_index'] == row['declaration_record_index']
    old_missing = {r['protocol'] for r in inventory['unresolved_protocols']}
    newly_linked = sorted(old_missing.intersection(found))
    assert all(sha(R / name) == h for name, h in frozen.items())
    assert sha(source) == source_hash
    out = R / 'experiments/protocol_source_exposure_resolution_v1_2026-10-15'
    out.mkdir()
    value = dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 bindings={str(source): source_hash, str(Path(__file__)): sha(__file__),
                           str(R / 'tools/archive_design_exposure_v3.py'): sha(R / 'tools/archive_design_exposure_v3.py')},
                 protocol_count=len(frozen), exact_snapshot_hash_edges=sum(map(len, edges.values())),
                 direct_valid_declaration_protocols=len(direct),
                 protocols_with_a_verified_declaration_chain=len(found),
                 previously_unresolved_linked_count=len(newly_linked),
                 previously_unresolved_linked=newly_linked,
                 remaining_unresolved_protocols=sorted(set(frozen).difference(found)),
                 witness_by_protocol=found,
                 mismatched_snapshot_reference_edges=mismatches,
                 out_of_snapshot_or_relative_protocol_reference_counts=dict(outside),
                 strict_unseen_families_certified=0,
                 all_witness_edges_independently_checked=True,
                 resource_admission=dict(shared_headroom_bytes=free, child_limit_bytes=limit,
                                         active_audit_reservation_bytes=8*2**30, margin_bytes=8*2**30),
                 scope='Frozen local protocol snapshot only. One exact hash-bound declaration chain per reached protocol; does not prove complete source coverage, source bytes, successful execution or model/label exposure. Non-protocol artifacts, unknown relative bases, mismatched versions, cross-project and global history remain unresolved. No new label or frontend/routing task opened.')
    (out / 'verification.json').write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({k: v for k, v in value.items() if k in (
        'protocol_count', 'exact_snapshot_hash_edges', 'direct_valid_declaration_protocols',
        'protocols_with_a_verified_declaration_chain', 'previously_unresolved_linked_count',
        'strict_unseen_families_certified')}))


if __name__ == '__main__':
    main()
