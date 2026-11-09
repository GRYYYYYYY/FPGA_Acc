"""Read-only selected source metadata; hash identity and name hints stay distinct."""
import datetime
import hashlib
import json
import re
import resource
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from archive_design_exposure_v3 import sha

R = Path(__file__).resolve().parents[1]
SELECT = re.compile(r'(manifest|cases?|input|source|capture|acquisition|prereg|protocol|freeze)', re.I)
EXCLUDE = re.compile(r'(?:^|[_.-])(results?|metrics?|qor)(?:[_.-]|$)', re.I)
HEX = re.compile('[0-9a-f]{64}')
PROJECTS = ('persistroute', 'tileplace', 'dieroute', 'fusionpar', 'experiments')


def strings(value, location=()):
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield location + ('<key>',), key
            yield from strings(item, location + (str(key),))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from strings(item, location + (str(i),))
    elif isinstance(value, str):
        yield location, value


def name_hint(value, names):
    if '\n' in value or len(value) > 4096:
        return None
    # Explicit whole basename forms only. No substring/fuzzy family inference.
    base = Path(value).name
    if base in names:
        return base
    for suffix in ('.v', '.sv', '.blif', '.eblif', '.pre-vpr.blif'):
        if base.endswith(suffix) and base[:-len(suffix)] in names:
            return base[:-len(suffix)]
    return None


def main():
    limit = 256 * 2**20
    free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= limit + 8 * 2**30, 'Metadata scan deferred by shared memory gate'
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    inventory = R / 'experiments/koios_pinned_source_inventory_v4_2026-10-15/verification.json'
    source = json.loads(inventory.read_text())
    members = source['all_benchmark_members']
    names = {Path(row['source']).stem: row for row in members}
    assets = {row['relative_to_official_VTR']: row for row in source['authenticated_files']}
    by_hash = defaultdict(list)
    for row in members:
        by_hash[assets[row['source']]['sha256']].append(row['source'])
    hashes = {}
    hits = []
    skipped = []
    discovery = {}
    for project in PROJECTS:
        root = R.parent / project
        cmd = ['rg', '--files', '--hidden', '--no-ignore', '-g', '*.json',
               '-g', '!**/third_party/**', '-g', '!**/build*/**', '-g', '!**/.ipcache/**', str(root)]
        listing = subprocess.run(cmd, text=True, capture_output=True)
        assert listing.returncode in (0, 1), listing.stderr
        paths = sorted(Path(x) for x in listing.stdout.splitlines()
                       if SELECT.search(Path(x).name) and not EXCLUDE.search(Path(x).name))
        discovery[project] = dict(json_files_discovered=len(listing.stdout.splitlines()),
                                  selected_source_metadata=len(paths))
        for path in paths:
            try:
                before = path.stat()
                if before.st_size > 2 * 2**20:
                    skipped.append(dict(path=str(path), reason='above2MiB_decode_cap', bytes=before.st_size))
                    continue
                raw = path.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                data = json.loads(raw)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or sha(path) != digest:
                    skipped.append(dict(path=str(path), reason='changed_during_read'))
                    continue
                hashes[str(path)] = digest
                for location, value in strings(data):
                    if value in by_hash:
                        hits.append(dict(project=project, metadata=str(path), metadata_sha256=digest,
                                         json_location=list(location), match_kind='declared_hash_equals_authenticated_raw_RTL',
                                         declared_sha256=value, matching_raw_RTL=by_hash[value]))
                    else:
                        name = name_hint(value, names)
                        if name is not None:
                            hits.append(dict(project=project, metadata=str(path), metadata_sha256=digest,
                                             json_location=list(location), match_kind='literal_name_hint_only',
                                             declared_string=value, hinted_source=names[name]['source'],
                                             provisional_group=names[name]['provisional_group']))
            except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as error:
                skipped.append(dict(path=str(path), reason=type(error).__name__))
    changed = set()
    for path, digest in hashes.items():
        try:
            if sha(path) != digest:
                changed.add(path)
        except FileNotFoundError:
            changed.add(path)
    stable_hits = [row for row in hits if row['metadata'] not in changed]
    for path in changed:
        skipped.append(dict(path=path, reason='changed_before_scan_finish'))
    stable_hashes = {path: digest for path, digest in hashes.items() if path not in changed}
    out = R / 'experiments/cross_project_koios_source_declarations_v1_2026-10-15'
    out.mkdir()
    summary = dict(selected_metadata=sum(row['selected_source_metadata'] for row in discovery.values()),
                   stable_decoded_metadata=len(stable_hashes), skipped_metadata=len(skipped),
                   stable_source_hint_records=len(stable_hits),
                   match_kind_counts=dict(Counter(row['match_kind'] for row in stable_hits)),
                   project_hit_counts=dict(Counter(row['project'] for row in stable_hits)),
                   hinted_groups=sorted({row['provisional_group'] for row in stable_hits if 'provisional_group' in row}))
    result = dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  bindings={str(inventory): sha(inventory), str(Path(__file__)): sha(__file__),
                            str(R/'tools/archive_design_exposure_v3.py'): sha(R/'tools/archive_design_exposure_v3.py')},
                  selection=dict(filename_regex=SELECT.pattern, excluded_filename_regex=EXCLUDE.pattern,
                                 projects=list(PROJECTS), no_ignore=True,
                                 excluded=['**/third_party/**', '**/build*/**', '**/.ipcache/**'],
                                 per_file_decode_cap_bytes=2*2**20),
                  discovery=discovery, summary=summary,
                  stable_metadata_sha256=stable_hashes,
                  source_declaration_or_name_hint_records=stable_hits,
                  skipped_metadata=skipped,
                  strict_unseen_families_certified=0,
                  new_frontend_or_route_jobs_launched=False,
                  resource_admission=dict(shared_headroom_bytes=free, address_space_limit_bytes=limit, margin_bytes=8*2**30),
                  scope='Read-only selected sibling-project source metadata snapshot. Exact raw RTL SHA declarations and literal whole-name hints are distinct; neither proves actual successful execution or exposure to labels. Name hints do not authenticate BLIF-to-RTL lineage or family identity. Other filenames, third-party/build trees, skipped/changing files, current/future writes and global history remain unknown. Native route files, demand labels and result metrics are not scan inputs. Absence never establishes unseen status.')
    (out/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
