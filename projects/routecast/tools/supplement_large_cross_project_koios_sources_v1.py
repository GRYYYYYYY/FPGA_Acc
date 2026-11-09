"""Decode the nine previously size-excluded source manifests, without label files."""
import datetime
import json
import resource
from collections import Counter
from pathlib import Path

from archive_design_exposure_v3 import sha
from inventory_cross_project_koios_source_declarations_v1 import strings, name_hint

R = Path(__file__).resolve().parents[1]


def role(path, value):
    # A copied compiler source tree may contain an entire benchmark distribution.
    # Do not call those benchmarks selected designs merely because they are shipped.
    if (path.name == 'source_manifest.json'
            and isinstance(value.get('files_sha256'), dict)
            and 'excluded_directory_prefixes' in value
            and any('/vpr/src/' in name for name in value['files_sha256'])):
        return 'compiler_source_package_inventory'
    if value.get('schema') == 'FUSIONPAR_VPR_BUNDLE_V1' and isinstance(value.get('inputs'), dict):
        return 'design_bundle_metadata'
    return 'unknown_metadata_role'


def main():
    limit = 192 * 2**20
    free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= limit + 8 * 2**30, 'Metadata supplement deferred by shared memory gate'
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    previous = R / 'experiments/cross_project_koios_source_declarations_v1_2026-10-15/verification.json'
    pinned = R / 'experiments/koios_pinned_source_inventory_v4_2026-10-15/verification.json'
    old = json.loads(previous.read_text())
    inventory = json.loads(pinned.read_text())
    names = {Path(x['source']).stem: x for x in inventory['all_benchmark_members']}
    assets = {x['relative_to_official_VTR']: x for x in inventory['authenticated_files']}
    hashes = {assets[x['source']]['sha256']: x['source'] for x in inventory['all_benchmark_members']}
    bindings = {str(p): sha(p) for p in (previous, pinned, Path(__file__),
                R/'tools/archive_design_exposure_v3.py',
                R/'tools/inventory_cross_project_koios_source_declarations_v1.py')}
    rows = []
    for skipped in old['skipped_metadata']:
        assert skipped['reason'] == 'above2MiB_decode_cap'
        path = Path(skipped['path'])
        before = path.stat()
        assert before.st_size <= 4 * 2**20
        digest = sha(path)
        value = json.loads(path.read_bytes())
        after = path.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
        assert sha(path) == digest
        metadata_role = role(path, value)
        hits = []
        for loc, text in strings(value):
            if text in hashes:
                hits.append(dict(json_location=list(loc), match_kind='declared_raw_RTL_hash',
                                 declared_sha256=text, source=hashes[text]))
            else:
                hint = name_hint(text, names)
                if hint is not None:
                    hits.append(dict(json_location=list(loc), match_kind='literal_name_hint_only',
                                     declared_string=text, source=names[hint]['source']))
        rows.append(dict(path=str(path), sha256=digest, bytes=after.st_size,
                         metadata_role=metadata_role, source_records=hits))
        bindings[str(path)] = digest
    assert len(rows) == 9
    for path, digest in bindings.items():
        assert sha(path) == digest
    out = R/'experiments/cross_project_large_source_supplement_v1_2026-10-15'
    out.mkdir()
    result = dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  bindings=bindings, all_nine_decoded_and_stable=True,
                  files=rows,
                  metadata_roles=dict(Counter(x['metadata_role'] for x in rows)),
                  source_record_counts_by_role={kind: sum(len(x['source_records']) for x in rows if x['metadata_role']==kind)
                                               for kind in sorted({x['metadata_role'] for x in rows})},
                  source_package_presence_is_design_use=False,
                  strict_unseen_families_certified=0,
                  resource_admission=dict(shared_headroom_bytes=free, address_space_limit_bytes=limit, margin_bytes=8*2**30),
                  scope='Nine size exclusions resolved by strict complete JSON parsing with 192MiB address-space cap. Compiler package file/hash inventory is not a selected design or model/label-use certificate. Package source presence does not disqualify an otherwise unseen design. Design-bundle paths and all name hints remain declarations, not lineage or successful execution. No native route or demand label file opened, no frontend/routing jobs launched. Other discovery exclusions and global history remain unknown.')
    (out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('all_nine_decoded_and_stable', 'metadata_roles',
                                          'source_record_counts_by_role', 'strict_unseen_families_certified')}))


if __name__ == '__main__':
    main()
