"""Exercise all congestion presets through the actual host and independent state replay."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import sys
from rr_present_schedule_replay import replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    host, output = args.host.resolve(), args.output.resolve()
    output.mkdir(exist_ok=False)
    nodes = [(0, 2, 0), (2, 0, 1), (2, 0, 1), (2, 2, 0), (4, 0, 1), (4, 0, 1)]
    edges = [(1, 3, 1), (2, 3, 1), (4, 3, 1), (5, 3, 1)]
    resources = [(0, 1, 256, 0, 0, 0xffffffff) for _ in nodes]
    tasks = [(0, 7, 0, 1, 0, 8, 0, 0, 0), (1, 7, 0, 2, 0, 8, 1, 0, 0),
             (2, 8, 3, 4, 0, 8, 2, 0, 0), (3, 8, 3, 5, 0, 8, 3, 0, 0)]
    for suffix, layout, rows in [('nodes', '<IHH', nodes), ('edges', '<IHH', edges),
                                  ('resources', '<HHHHII', resources), ('tasks', '<IIIIHHIII', tasks)]:
        (output / ('input.' + suffix)).write_bytes(b''.join(struct.pack(layout, *r) for r in rows))
    (output / 'topology.node_die').write_bytes(bytes(2 * len(nodes)))
    (output / 'topology.node_box').write_bytes(bytes(8 * len(nodes)))
    timing = output / 'fixed_fixture_timing.py'
    timing.write_text('''import csv,sys
with open(sys.argv[2]) as stream: rows=list(csv.DictReader(stream))
with open(sys.argv[3],'w') as stream:
 writer=csv.writer(stream,lineterminator='\\n')
 writer.writerow(['task_id','criticality_q','delay_ps','slack_ps','critical_path_delay_ps'])
 for row in rows: writer.writerow([row['task_id'],0,row['delay_ps'],0,1])
''')
    cases, files = [], [Path(__file__).resolve(), host, timing]
    for mode in range(3):
        for width in (4,):
            epochs = 30 if mode == 0 else 60
            prefix = output / f'mode{mode}_issue{width}'
            env = {k: v for k, v in os.environ.items() if not k.startswith(('DIEROUTE_', 'PERSISTROUTE_'))}
            env.update(DIEROUTE_COST_BITS='64', DIEROUTE_VPR_STYLE_COST='1',
                       DIEROUTE_TREE_TIMING_WEIGHT_Q='128', DIEROUTE_LOCAL_TASK_ORDER='0',
                       DIEROUTE_ORDINARY_SCHEDULE_MODE="0", DIEROUTE_PRESENT_SCHEDULE_MODE=str(mode), DIEROUTE_ISSUE_WIDTH=str(width),
                       DIEROUTE_MIN_TIMING_ITERATIONS=str(epochs), DIEROUTE_MAX_ITERATIONS=str(epochs),
                       PERSISTROUTE_TIMING_COMMAND=shlex.join([sys.executable, str(timing)]))
            command = [str(host), str(output / 'input'), str(output / 'topology'), str(prefix), 'flat']
            with Path(str(prefix) + '.log').open('w') as log:
                subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
            result = replay(output / 'input', prefix, 0, width, epochs, present_mode=mode)
            assert result['cpu_legal'] and result['epochs'] == epochs and result['ripup_events'] == 2*(epochs-1)
            counters = json.loads(Path(str(prefix) + '.json').read_text())
            assert counters['present_schedule_mode'] == mode and counters['ordinary_schedule_mode'] == 0 and counters['ordinary_ripup_events'] == 2*(epochs-1)
            cases.append(dict(name=prefix.name, command=command, counters_sha256=hashlib.sha256(
                Path(str(prefix) + '.json').read_bytes()).hexdigest(), replay=result))
            files += [Path(p) for p in result['source_sha256']]
    mutations = []
    for name, selected, suffix, field, value in [
            ('present_factor', 'mode2_issue4', 'iterations.csv', 'present_factor_q', 1),
            ('resource_version_hash', 'mode1_issue4', 'audit.csv', 'resource_hash', 0)]:
        bad = output / name
        bad.mkdir()
        for original in output.glob(selected + '.*'):
            (bad / ('trace' + original.name[len(selected):])).symlink_to(original)
        path = bad / ('trace.' + suffix)
        with path.open() as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        rows[-1][field] = str(value)
        path.unlink()
        with path.open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        try:
            mode = 2 if name == 'present_factor' else 1
            replay(output / 'input', bad / 'trace', 0, 4, 60, present_mode=mode)
        except AssertionError:
            mutations.append(dict(name=name, rejected=True, data_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        else:
            raise AssertionError('Incorrect present-factor/resource-version metadata passed')
    report = dict(status='actual_host_present_presets_transitions_caps_and_versions_replayed',
                  cases=cases, copied_fixture_mutations=mutations,
                  source_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  scope='Three actual CPU-host small-graph runs (legacy30 epochs,presets60 epochs) with fixed synthetic criticalities and CPD. '
                        'All factors, ripup fences, paths, epoch/final resource-cost versions replayed; two copied '
                        'metadata corruptions rejected. Not native timing quality, five-repeat evidence, '
                        'per-CU read-version receipts or physical performance.',
                  board_result=False, research_complete=False)
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], runs=len(cases), mutations=len(mutations))))


if __name__ == '__main__':
    main()
