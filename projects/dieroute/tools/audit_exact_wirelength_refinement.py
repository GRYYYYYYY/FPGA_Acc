"""Verify incremental search charges against complete native route wirelength."""
from pathlib import Path
import array
import collections
import csv
import hashlib
import json
import sys


def main():
    directory = Path(sys.argv[1]).resolve()
    refs = {}

    def read(path):
        path = Path(path)
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    def trees(path):
        path = Path(path)
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        nets = collections.defaultdict(set)
        with path.open() as stream:
            for row in csv.DictReader(stream):
                nets[int(row['net_id'])].update(int(row[k]) for k in ['source', 'parent', 'child'])
        return nets

    manifest = read(directory / 'manifest.json')
    assert manifest['status'].startswith('experiment_terminal_')
    assert read(directory / 'independent_audit.json')['status'] == 'private_refinement_monotone_native_acceptance_and_stop_reviewed'
    assert read(directory / 'policy_audit.json')['status'] == 'rounded_budgets_blocker_first_order_and_native_decisions_verified'
    counts = {'complete_search_trees': 0, 'rebuilt_net_charge_checks': 0, 'native_wirelength_checks': 0}
    for record in manifest['stages']:
        stage = directory / ('stage_' + str(record['iteration']).zfill(3))
        protocol_file = stage / 'exchange/protocol.json'
        if not protocol_file.exists():
            continue
        protocol = read(protocol_file)
        assert protocol['search_objective'] == 'wirelength'
        weight_path = Path(protocol['wirelength_weights'])
        raw = weight_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == protocol['source_sha256'][str(weight_path)]
        refs[str(weight_path)] = digest
        weights = array.array('H')
        weights.frombytes(raw)
        if sys.byteorder != 'little':
            weights.byteswap()
        generated = read(stage / 'exchange/manifest.json')
        for arm in generated['arms']:
            if not arm.get('candidate_tree'):
                continue
            nets = trees(arm['candidate_tree'])
            for step in arm['steps']:
                charged = sum(s['wirelength'] for s in step['searches'])
                actual = sum(weights[n] for n in nets[step['net']])
                assert charged == actual, (record['iteration'], arm['name'], step['net'], charged, actual)
                counts['rebuilt_net_charge_checks'] += 1
            counts['complete_search_trees'] += 1
        for audit_path in record.get('candidate_audits', []):
            audit = read(audit_path)
            tree = Path(audit_path).parent / 'candidate/route.route_trees.csv'
            computed = sum(weights[n] for nodes in trees(tree).values() for n in nodes)
            assert computed == audit['wirelength']
            counts['native_wirelength_checks'] += 1
    refs[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = {'status': 'incremental_wire_charges_and_native_totals_verified',
              'checks': counts, 'source_sha256': refs, 'research_complete': False,
              'scope': 'Observed terminal experiment only. Exact per-net incremental charge conservation and full native tree totals. No global multi-net optimality, generalization or board result.'}
    with (directory / 'wirelength_audit.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'checks': counts}))


if __name__ == '__main__':
    main()
