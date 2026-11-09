#!/usr/bin/env python3
"""Exercise checkpoint binding and semantic identity rejection on disposable copies."""
import argparse
import copy
import json
from pathlib import Path
import tempfile

from audit_tp_checkpoint_reference import audit
from run_development import sha


def binding(path):
    return {'path': str(path.resolve()), 'sha256': sha(path)}


def check(reference, output):
    if output.exists():
        raise ValueError('output already exists')
    original = json.loads(reference.read_text())
    digest = sha(reference)
    results = []
    with tempfile.TemporaryDirectory(prefix='fusionpar-checkpoint-negative-') as temp:
        root = Path(temp)
        for mode, expected in (
                ('wrong_certificate', 'another canonical output'),
                ('changed_block_identity', 'coordinates/identity')):
            altered = copy.deepcopy(original)
            row = altered['designs']['ex5p']['population'][1]
            closure = json.loads(Path(row['closure']['path']).read_text())
            if mode == 'wrong_certificate':
                closure['placement_validation']['placement_sha256'] = '0' * 64
            else:
                golden = Path(closure['inputs']['golden_place']['path'])
                lines = golden.read_text().splitlines()
                for i, line in enumerate(lines):
                    fields = line.split()
                    if len(fields) >= 6 and fields[5].startswith('#') and fields[5][1:].isdigit():
                        fields[5] = '#' + str(int(fields[5][1:]) + 100000)
                        lines[i] = '\t'.join(fields)
                        break
                else:
                    raise ValueError('no placement row found for negative control')
                changed = root / 'changed.place'
                changed.write_text('\n'.join(lines) + '\n')
                closure['inputs']['golden_place'] = binding(changed)
            closure_path = root / (mode + '_closure.json')
            closure_path.write_text(json.dumps(closure))
            row['closure'] = binding(closure_path)
            reference_path = root / (mode + '.json')
            reference_path.write_text(json.dumps(altered))
            try:
                audit(reference_path)
            except ValueError as error:
                if expected not in str(error):
                    raise
                results.append({'case': mode, 'rejected': True, 'reason': str(error)})
            else:
                raise ValueError('corrupt checkpoint accepted: ' + mode)
    if sha(reference) != digest:
        raise ValueError('original reference changed')
    result = {'schema': 'FUSIONPAR_TP_CHECKPOINT_NEGATIVE_CONTROLS_V1', 'pass': True,
              'reference': binding(reference), 'checker': binding(Path(__file__)),
              'auditor': binding(Path(__file__).with_name('audit_tp_checkpoint_reference.py')),
              'cases': results}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'pass': True, 'rejected_controls': len(results)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(args.reference, args.output)
