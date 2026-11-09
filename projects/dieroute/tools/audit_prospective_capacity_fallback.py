"""Check fallback seed rules, exact net mixtures, capacities and native selection."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import mmap
import struct
import sys


def main():
    directory = Path(sys.argv[1]).resolve()
    refs = {}

    def read(path):
        path = Path(path)
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    def verify(document):
        for name, expected in document['source_sha256'].items():
            digest = hashlib.sha256(Path(name).read_bytes()).hexdigest()
            assert digest == expected, name
            refs[name] = digest

    result = read(directory / 'fallback_result.json')
    verify(result)
    selection = read(directory / 'observation/selection.json')
    verify(selection)
    selected = [v['task'] for v in selection['selected'][:2]]
    if result['status'] == 'capacity_fallback_no_regressed_critical_targets':
        assert not selected and not result['joint_quality_pass']
        reviewed = []
        chosen_audit = None
    else:
        assert result['status'] == 'preregistered_capacity_fallback_terminal_reviewed' and selected
        protocol = read(directory / 'protocol.json')
        verify(protocol)
        generation = read(directory / 'manifest.json')
        construction = read(directory / 'closure_construction.json')['closures']
        plans = [[task] for task in selected] + ([selected] if len(selected) == 2 else [])
        assert [v['seed_tasks'] for v in construction] == plans

        def tree(path):
            path = Path(path)
            refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            nets = collections.defaultdict(set)
            with path.open() as stream:
                for row in csv.DictReader(stream):
                    nets[int(row['net_id'])].add(tuple(int(row[k]) for k in ['net_id', 'source', 'parent', 'child']))
            return nets

        baseline = tree(protocol['baseline_tree'])
        candidate = tree(protocol['candidate_tree'])
        with Path(protocol['connections']).open() as stream:
            tasks = {int(row['id']): int(row['net_id']) for row in csv.DictReader(stream)}
        reviewed = []
        groups = {}
        with Path(protocol['resources']).open('rb') as stream:
            capacities = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ)
            for closure, arm in zip(construction, generation['arms']):
                assert closure['name'] == arm['name']
                restored = set(closure['restored_nets'])
                assert {tasks[t] for t in closure['seed_tasks']} <= restored <= baseline.keys()
                actual = tree(arm['candidate_tree'])
                assert set(actual) == set(candidate) == set(baseline)
                occupancy = collections.Counter()
                for net, rows in actual.items():
                    assert rows == (baseline[net] if net in restored else candidate[net])
                    occupancy.update({v for row in rows for v in row[1:]})
                assert all(count <= struct.unpack_from('<H', capacities, 16 * node + 2)[0] for node, count in occupancy.items())
                assert closure['waves'][-1]['overused_resources'] == 0
                digest = hashlib.sha256(Path(arm['candidate_tree']).read_bytes()).hexdigest()
                assert digest == arm['candidate_tree_sha256']
                groups.setdefault(digest, []).append(arm['name'])
                reviewed.append({'arm': arm['name'], 'restored_nets': len(restored),
                                 'total_nets': len(actual), 'retained_candidate_nets': len(actual) - len(restored)})
            capacities.close()
        assert len(construction) == len(generation['arms']) == result['generated_arms']
        queue = read(directory / 'native_queue/protocol.json')
        assert queue['deduplicated_generation_groups'] == groups
        assert [v['net'] for v in queue['cases']] == [v[0] for v in groups.values()]
        assert [v['arm'] for v in result['outcomes']] == [v['net'] for v in queue['cases']]
        assert result['unique_native_candidates'] == len(groups)
        eligible = []
        audits = {}
        for outcome in result['outcomes']:
            audit = read(outcome['audit'])
            verify(audit)
            assert outcome['checks'] == audit['checks']
            audits[outcome['arm']] = outcome['audit']
            if all(audit['checks'].values()):
                eligible.append((audit['cpd_ns'], audit['wirelength'], audit['model_crossings'], outcome['arm']))
        chosen = min(eligible)[3] if eligible else None
        assert chosen == result['selected_arm'] and result['joint_quality_pass'] == (chosen is not None)
        chosen_audit = audits[chosen] if chosen is not None else None
    refs[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = {'status': 'prospective_capacity_fallback_mixture_capacity_and_native_selection_reviewed',
              'label': result['label'], 'joint_quality_pass': result['joint_quality_pass'],
              'closures': reviewed, 'selected_native_audit': chosen_audit, 'source_sha256': refs,
              'scope': 'Exact recorded baseline/candidate net mixtures, actual capacities, fixed task seeds, deduplication and all unique native gate decisions. Not proof of minimum restoration or optimal search, independent circuit generalization or board performance.',
              'research_complete': False}
    with (directory / 'fallback_audit.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'label': result['label'], 'joint_quality_pass': result['joint_quality_pass'], 'closures': len(reviewed)}))


if __name__ == '__main__':
    main()
