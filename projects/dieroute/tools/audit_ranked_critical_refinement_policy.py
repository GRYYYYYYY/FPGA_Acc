"""Audit rounded budgets, execution order and rejected native candidates."""
from pathlib import Path
from decimal import Decimal
import csv
import hashlib
import json
import sys


def main():
    directory = Path(sys.argv[1]).resolve()
    refs = {}

    def sha(path):
        path = Path(path)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
        refs[str(path)] = digest.hexdigest()
        return refs[str(path)]

    def read(path, sources=False):
        value = json.loads(Path(path).read_text())
        sha(path)
        if sources:
            for name, expected in value['source_sha256'].items():
                assert sha(name) == expected, name
        return value

    basic = read(directory / 'independent_audit.json', True)
    assert basic['status'] == 'private_refinement_monotone_native_acceptance_and_stop_reviewed'
    manifest = read(directory / 'manifest.json')
    reviewed = []
    for record in manifest['stages']:
        stage = directory / ('stage_' + str(record['iteration']).zfill(3))
        protocol_file = stage / 'exchange/protocol.json'
        if not protocol_file.exists():
            assert record['status'] in ['no_positive_worst_slack_regression', 'diagnosis_search_incomplete', 'no_untried_regressed_critical_connection']
            continue
        protocol = read(protocol_file, True)
        with (stage / 'observation/parent/native_observations.csv').open() as stream:
            printed_cpds = {int(v['critical_path_delay_ps']) for v in csv.DictReader(stream)}
        assert printed_cpds == {protocol['connection_ceiling_cpd_ps']}
        assert protocol['blockers_first'] is True
        generated = read(stage / 'exchange/manifest.json')
        arms = {v['name']: v for v in protocol['arms']}
        for arm in generated['arms']:
            expected = [*arms[arm['name']]['order'], arm['target']]
            actual = [step['net'] for step in arm['steps']]
            assert actual == expected[:len(actual)]
            if arm.get('candidate_tree'):
                assert actual == expected
                assert sha(arm['candidate_tree']) == arm['candidate_tree_sha256']
        eligible = []
        for name in record.get('candidate_audits', []):
            audit = read(name, True)
            checks = audit['checks']
            if all(checks[k] for k in ['native_legal', 'capacity', 'wirelength', 'modeled_transitions']) and (Decimal(str(audit['cpd_ns'])), audit['wirelength'], audit['model_crossings']) < (Decimal(str(record['input']['cpd_ns'])), record['input']['wirelength'], record['input']['model_crossings']):
                eligible.append(name)
        if record['status'] == 'no_strict_private_lexicographic_improvement':
            queue = read(stage / 'exchange/native_queue/protocol.json')
            assert len(record['candidate_audits']) == len(queue['cases'])
            assert not eligible
        if record['status'] == 'strict_private_improvement':
            assert record['output']['audit'] in eligible
        reviewed.append({'stage': record['iteration'], 'rounded_ceiling_ps': next(iter(printed_cpds)),
                         'status': record['status'], 'eligible_candidates': len(eligible)})
    sha(Path(__file__).resolve())
    result = {'status': 'rounded_budgets_blocker_first_order_and_native_decisions_verified',
              'stages': reviewed, 'source_sha256': refs, 'research_complete': False,
              'scope': 'Supplement to terminal acceptance-chain audit. Observed private stages only; no generalization, board result or full research completion.'}
    with (directory / 'policy_audit.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'stages': len(reviewed)}))


if __name__ == '__main__':
    main()
