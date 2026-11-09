"""Adapt frozen native indexed-cost export to an audited prospective cohort."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roundtrip', type=Path)
    parser.add_argument('baselines', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    roundtrip = args.roundtrip.resolve()
    baselines = args.baselines.resolve()
    output = args.output.resolve()
    audit = json.loads((roundtrip / 'independent_audit.json').read_text())
    assert audit['status'] == 'five_prospective_apex2_full_graph_node_edge_and_native_noop_roundtrips_independently_reviewed'
    rows = audit['cases']
    assert [v['label'] for v in rows] == ['apex2_seed' + str(s) for s in range(6, 11)]
    old = root / 'work/reserved_apex2_native_costs_20261017'
    output.mkdir()
    shutil.copytree(old / 'tools', output / 'tools', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    script = (old / 'supervise.py').read_text().replace('five_reserved_apex2_', 'five_prospective_apex2_')
    script = script.replace("protocol=json.loads((p/'protocol.json').read_text())",
                            "assert not (p/'manifest.json').exists();protocol=json.loads((p/'protocol.json').read_text())")
    (output / 'supervise.py').write_text(script)
    cases = [{'label': v['label'], 'native_case': str(baselines / v['label']),
              'original_input': str(roundtrip / v['label'] / 'input'),
              'nodes': v['nodes'], 'edges': v['edges']} for v in rows]
    files = [roundtrip / 'independent_audit.json', baselines / 'candidate_policy.json', Path(__file__).resolve()]
    files.extend(f for f in (output / 'tools').rglob('*') if f.is_file())
    for case in cases:
        files.extend(Path(case['original_input'] + '.' + ext) for ext in ['nodes', 'edges', 'resources', 'tasks'])
        files.append(Path(case['native_case']) / 'run.json')
    def hashes(paths):
        return {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
    protocol = {'status': 'frozen_before_launch', 'cases': cases, 'inputs': hashes(files),
                'scope': 'Unchanged frozen exporter/rebaser; all five prospective cases, native indexed base costs and exact other-byte preservation. No routing-policy tuning, candidate benefit or board claim.',
                'research_complete': False, 'board_result': False}
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    (output / 'launch_protocol.json').write_text(json.dumps({'inputs': hashes([output / 'protocol.json', output / 'supervise.py'])}, indent=2) + '\n')
    print(json.dumps({'prepared_cases': len(cases), 'directory': str(output)}), flush=True)
    if args.run:
        subprocess.run([sys.executable, str(output / 'supervise.py')], cwd=root, check=True)


if __name__ == '__main__':
    main()
