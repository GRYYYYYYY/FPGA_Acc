"""Freeze local family candidates before predictions; never infer unseen from absence."""
import datetime
import hashlib
import json
import shutil
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    vtr = root.parent / 'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    bench = vtr / 'vtr_flow/benchmarks'
    out = root / 'experiments/prospective_family_candidates_2026-10-06'
    out.mkdir()
    records = []
    groups = {'vexriscv': sorted((bench / 'vexriscv').glob('*.v')),
              'arithmetic': sorted((bench / 'arithmetic').rglob('*.v')),
              'riscv_mapped_origin_unresolved': [bench / 'tests/riscv_core_lut6.blif']}
    protocols = sorted((root / 'experiments').rglob('protocol.json'))
    texts = [(str(p.relative_to(root)), p.read_text(errors='replace')) for p in protocols]
    for family, paths in groups.items():
        for path in paths:
            sha = digest(path)
            archived = out / 'inputs' / path.relative_to(bench)
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, archived)
            assert digest(archived) == sha == digest(path)
            matches = [p for p, text in texts if sha in text or str(path) in text or path.name in text]
            records.append({'family_candidate': family, 'original_path': str(path),
                            'archived_path': str(archived.relative_to(root)), 'sha256': sha,
                            'protocol_text_matches': matches,
                            'unseen_family_status': 'unproven',
                            'mapped_origin_status': 'unresolved' if path.suffix == '.blif' else 'HDL requires authenticated frontend'})
    readme = bench / 'arithmetic/README.txt'
    shutil.copyfile(readme, out / 'arithmetic_README.txt')
    shutil.copyfile(__file__, out / 'source.py')
    manifest = {'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_sha256': digest(__file__), 'vtr_directory_revision_label': vtr.name,
                'revision_label_is_authenticated_commit': False,
                'arithmetic_readme_sha256': digest(readme),
                'records': records,
                'protocol_count_scanned': len(protocols),
                'scope': 'input and provenance candidate freeze only; no predictions/native labels evaluated',
                'required_before_holdout_claim': ['authenticate upstream dataset provenance and commit',
                    'audit related variants and indirect family exposure',
                    'freeze whole-family split and algorithm settings before measuring',
                    'authenticate mapped frontend and physical endpoint accounting'],
                'selection_policy': 'all local VexRiscv Verilog and arithmetic Verilog plus mapped RISC-V candidate; no QoR-based selection'}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    receipt = {'manifest_sha256': digest(out / 'manifest.json'), 'files': len(records),
               'family_candidates': {k: len(v) for k, v in groups.items()},
               'matched_records': sum(bool(r['protocol_text_matches']) for r in records),
               'unseen_family_claim': False}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
