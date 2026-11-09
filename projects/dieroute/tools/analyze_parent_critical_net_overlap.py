"""Join native critical-delay regressions to descriptive per-net wire changes."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    directory = Path(sys.argv[1]).resolve()
    refs, rows = {}, []

    def sha(path):
        h = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        refs[str(Path(path).resolve())] = h
        return h

    def load(path, key):
        sha(path)
        with path.open() as stream:
            values = list(csv.DictReader(stream))
        result = {int(v[key]): v for v in values}
        assert len(result) == len(values)
        return result

    for seed in [6, 7]:
        label = 'apex2_seed' + str(seed)
        case = directory / label
        audit_path = case / 'independent_audit.json'
        audit = json.loads(audit_path.read_text())
        assert audit['status'] == 'native_routed0_observations_provenance_and_quality_reviewed'
        for name, expected in audit['source_sha256'].items():
            assert sha(name) == expected, name
        baseline_path = case / 'baseline/native_observations.csv'
        parent_path = case / 'parent/native_observations.csv'
        selection = case / 'critical_selection.json'
        if not selection.exists():
            subprocess.run([sys.executable, str(root / 'tools/select_regressed_critical_connections.py'),
                            str(baseline_path), str(parent_path), str(selection)], check=True)
        selection_report = json.loads(selection.read_text())
        for name, expected in selection_report['source_sha256'].items():
            assert sha(name) == expected, name
        selected = selection_report['selected']
        baseline = load(baseline_path, 'task_id')
        parent = load(parent_path, 'task_id')
        connections = load(root / 'work/prospective_apex2_seeds6_10_roundtrip_20261020' / label / 'connections.csv', 'id')
        nets = load(root / 'work/prospective_parent_net_changes_20261020' / (label + '_nets.csv'), 'net_id')
        assert baseline.keys() == parent.keys() == connections.keys()
        joined = []
        for item in selected:
            task = item['task']
            net = int(connections[task]['net_id'])
            # Native observation ABI identifies rows by task_id only. The audited
            # routed0 query binds that ID to the connection/net/source/sink.
            joined.append({**item, 'net_id': net, 'fanout': int(nets[net]['fanout']),
                           'wirelength_delta': int(nets[net]['wirelength_delta']),
                           'crossing_delta': int(nets[net]['crossing_delta'])})
        rows.append({'label': label, 'selected_critical_regressions': joined,
                     'all_connections': len(parent),
                     'connections_with_delay_increase': sum(int(parent[t]['delay_ps']) > int(baseline[t]['delay_ps']) for t in parent),
                     'critical_regressions_on_high_fanout_nets': sum(v['fanout'] >= 16 for v in joined),
                     'critical_regressions_on_lengthened_nets': sum(v['wirelength_delta'] > 0 for v in joined)})
        for path in [selection, audit_path]:
            sha(path)
    sha(Path(__file__))
    result = {'status': 'native_critical_regressions_joined_to_per_net_changes', 'rows': rows,
              'source_sha256': refs, 'research_complete': False,
              'scope': 'Read-only rounded-ps native observations of two failing frozen parents. Descriptive overlap, not causal proof or policy change; all selected worst-slack positive regressions retained.'}
    with (directory / 'critical_overlap.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
