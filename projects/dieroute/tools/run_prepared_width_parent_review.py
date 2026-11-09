"""Run one prepared posterior parent review only after successful routing."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prepared = root / 'work/width_coverage_pending_review_preparation_20261018'
    receipt = json.loads((prepared / 'manifest.json').read_text())
    matches = [r for r in receipt['records'] if r['label'] == args.label]
    if len(matches) != 1:
        parser.error('Label must identify exactly one prepared review')
    for relative, expected in receipt['source_sha256'].items():
        if hashlib.sha256((root / relative).read_bytes()).hexdigest() != expected:
            raise SystemExit('Preparation source hash mismatch: ' + relative)
    record = matches[0]
    protocol_path = root / record['protocol']
    if hashlib.sha256(protocol_path.read_bytes()).hexdigest() != record['sha256']:
        raise SystemExit('Prepared protocol hash mismatch')
    protocol = json.loads(protocol_path.read_text())
    cohort = json.loads((root / 'work/width_coverage_parents_20261018/manifest.json').read_text())
    rows = [r for r in cohort['steps'] if r['label'] == args.label]
    ready = len(rows) == 1 and rows[0]['status'] == 'passed' and rows[0].get('returncode') == 0
    if args.check_only:
        print(json.dumps({'label': args.label, 'protocol_hash_verified': True,
                          'parent_successfully_terminal': ready, 'launched': False}))
        return
    if not ready:
        raise SystemExit('Parent is not successfully terminal; review not launched')
    destination = root / 'work' / ('width_parent_review_' + args.label + '_20261018')
    destination.mkdir(exist_ok=False)
    (destination / 'protocol.json').write_bytes(protocol_path.read_bytes())
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('DIEROUTE', 'PERSISTROUTE'))}
    completed = []
    manifest = {'status': 'running', 'pid': os.getpid(), 'steps': completed,
                'research_complete': False, 'board_result': False}
    def save():
        temporary = destination / 'manifest.tmp'
        temporary.write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.replace(destination / 'manifest.json')
    save()
    for step in protocol['steps']:
        started = time.monotonic_ns()
        with (destination / (step['label'] + '.log')).open('x') as log:
            result = subprocess.run(step['command'], cwd=root, env=env,
                                    stdout=log, stderr=subprocess.STDOUT)
        completed.append(dict(step, returncode=result.returncode,
                              wall_ns=time.monotonic_ns() - started))
        if result.returncode:
            manifest['status'] = 'failed'
            save()
            raise SystemExit(result.returncode)
        save()
    manifest['status'] = 'review_commands_terminal_requires_evidence_interpretation'
    save()
    print(json.dumps({'status': manifest['status'], 'directory': str(destination)}))


if __name__ == '__main__':
    main()
