"""Compare final path local-RC sums with native routed connection delays."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(pair, out):
    m = json.loads((pair / 'pair.json').read_text())
    assert m['status'] == 'completed'
    out.mkdir(exist_ok=False)
    reference = Path(m['reference'])
    prefix = pair / 'input' if 'native_cost_export' in m else reference / 'input'
    nodes = list(struct.iter_unpack('<IHH', Path(str(prefix)+'.nodes').read_bytes()))
    edges = list(struct.iter_unpack('<IHH', Path(str(prefix)+'.edges').read_bytes()))
    paths = {}
    with (pair / 'downstream_bounded_0.paths.csv').open() as stream:
        for row in csv.DictReader(stream):
            task = int(row['task_id'])
            paths.setdefault(task, []).append((int(row['path_index']), int(row['resource_id'])))
    with (reference / 'connections.csv').open() as stream:
        tasks = list(csv.DictReader(stream))
    estimates = {}
    input_path = out / 'native_input.csv'
    with input_path.open('w') as stream:
        writer = csv.writer(stream)
        writer.writerow(['iteration','task_id','net_id','source','sink','routed','delay_ps','criticality_q'])
        for task in tasks:
            ident = int(task['id']); source = int(task['source'])
            rows = sorted(paths.get(ident, []))
            assert [r[0] for r in rows] == list(range(len(rows)))
            assert rows and rows[-1][1] == int(task['sink'])
            total = 0
            for _, child in rows:
                begin, count, _ = nodes[source]
                assert begin + count <= len(edges), 'Node CSR exceeds edge buffer'
                delays = [delay for dst, _, delay in edges[begin:begin+count] if dst == child]
                assert delays, (source, child)
                total += min(delays); source = child
            estimates[ident] = total
            # routed=0 asks the existing hook to retain native net_delay.
            writer.writerow([0,ident,task['net_id'],task['source'],task['sink'],0,0,task['criticality_q']])
    env = {k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_', 'PERSISTROUTE_'))}
    env.update(m['timing_environment'])
    env['PERSISTROUTE_VPR_ROUTE'] = str(pair / 'downstream_bounded.route')
    adapter = pair / 'source/persistroute/tools/vpr_timing_analyzer.py'
    output_path = out / 'native_output.csv'
    command = ['python3', str(adapter), '0', str(input_path), str(output_path)]
    files = [pair/'pair.json', reference/'connections.csv', pair/'downstream_bounded_0.paths.csv',
             pair/'downstream_bounded.route', Path(str(prefix)+'.nodes'), Path(str(prefix)+'.edges'),
             adapter, Path(m['timing_vpr']['path'])]
    inputs = {str(p):sha(p) for p in files}
    manifest = dict(status='running', command=command, inputs=inputs, board_result=False)
    manifest_path = out / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    with (out/'run.log').open('w') as log:
        rc = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    manifest.update(returncode=rc, inputs_unchanged=all(sha(Path(p))==h for p,h in inputs.items()))
    manifest['status'] = 'failed' if rc else 'completed_requires_analysis'
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    assert rc == 0 and manifest['inputs_unchanged']
    with output_path.open() as stream:
        actual = {int(row['task_id']):row for row in csv.DictReader(stream)}
    assert actual.keys() == estimates.keys()
    cpds = {int(row['critical_path_delay_ps']) for row in actual.values()}
    assert len(cpds) == 1
    validation = json.loads((pair/'downstream_bounded_validation/validation.json').read_text())
    native_cpd = validation['critical_path_delay_ns'] * 1000
    assert abs(next(iter(cpds))-native_cpd) <= 1, 'Native extraction CPD disagrees with validation'
    rows = []
    for task in tasks:
        ident = int(task['id']); native = int(actual[ident]['delay_ps'])
        rows.append(dict(task_id=ident,net_id=int(task['net_id']),local_rc_ps=estimates[ident],
                         native_ps=native,error_ps=estimates[ident]-native))
    report = dict(status='measured',connections=len(rows),board_result=False,
                  scope='Final node-path minimum parallel-edge local-RC sums versus native full routed-tree delay; not a causal CPD proof',
                  mean_absolute_error_ps=sum(abs(r['error_ps']) for r in rows)/len(rows),
                  maximum_absolute_error_ps=max(abs(r['error_ps']) for r in rows),
                  native_cpd_ps=next(iter(cpds)), native_validation_cpd_ps=native_cpd,
                  routed_zero_rows_verified=len(tasks),
                  rows=rows, native_output_sha256=sha(output_path))
    (out/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    run(args.pair.resolve(),args.output.resolve())
