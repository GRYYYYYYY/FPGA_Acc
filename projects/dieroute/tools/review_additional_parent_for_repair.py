"""Retain every raw-parent review and classify eligibility for capacity repair."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from prepare_additional_fresh_parent import digest


def review(attempt):
    attempt = attempt.resolve()
    config = json.loads((attempt / 'parent_review_protocol.json').read_text())
    for name, expected in config['source_sha256'].items():
        assert digest(name) == expected, name
    directory = attempt / 'raw_parent_review'
    directory.mkdir(exist_ok=False)
    outcomes = []

    def run(kind, command):
        with (directory / (kind + '.stdout')).open('x') as out, (directory / (kind + '.stderr')).open('x') as err:
            child = subprocess.Popen(command, stdout=out, stderr=err,
                                     stdin=subprocess.DEVNULL)
            fields = Path('/proc', str(child.pid), 'stat').read_text().rsplit(')', 1)[1].split()
            receipt = {'kind': kind, 'command': command, 'pid': child.pid,
                       'start_ticks': fields[19], 'started_ns': time.time_ns()}
            (directory / (kind + '.launch.json')).write_text(json.dumps(receipt, indent=2) + '\n')
            code = child.wait()
        terminal = {**receipt, 'returncode': code, 'ended_ns': time.time_ns()}
        (directory / (kind + '.terminal.json')).write_text(json.dumps(terminal, indent=2) + '\n')
        outcomes.append(terminal)
        return code

    # No failed raw check is relabeled as a pass or silently omitted.
    for step in config['steps']:
        run(step['kind'], step['command'])
    parent = json.loads((attempt / 'recipe/pair.json').read_text())
    input_prefix = parent['steps'][0]['command'][1]
    classifier = Path(__file__).resolve().with_name('classify_parent_capacity_overuse.py')
    classification = directory / 'capacity_classification.json'
    code = run('classification', [sys.executable, str(classifier), input_prefix,
                                  str(attempt / 'parent/route'), '--report', str(classification)])
    original = {row['kind']: row['returncode'] for row in outcomes}
    classified = json.loads(classification.read_text()) if code == 0 else None
    structural = code == 0
    original_tree_explained = original['tree'] == 0 or (
        structural and classified['capacity_only_failure'])
    eligible = (structural and original_tree_explained and
                original['provenance'] == 0 and original['writeback'] == 0)
    report = {
        'status': 'raw_parent_checks_retained_repair_eligibility_classified',
        'label': config['label'], 'repair_eligible': eligible,
        'raw_parent_native_returncode': original['native'],
        'raw_parent_joint_pass_claim': False,
        'steps': outcomes,
        'source_sha256': {str(attempt / 'parent_review_protocol.json'):
                          digest(attempt / 'parent_review_protocol.json'),
                          str(classifier): digest(classifier),
                          str(Path(__file__).resolve()): digest(__file__)},
        'scope': 'Eligibility only. Raw native failure remains a failure; no native '
                 'pass inferred. Repaired tree must independently pass full tree, '
                 'capacity, sink identity and source-bound native quality checks. '
                 'Run under the standard descendant memory guard.',
        'research_complete': False,
    }
    if classified is not None:
        report['source_sha256'][str(classification)] = digest(classification)
    (attempt / 'parent_repair_eligibility.json').write_text(json.dumps(report, indent=2) + '\n')
    return eligible


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    sys.exit(0 if review(args.attempt) else 1)
