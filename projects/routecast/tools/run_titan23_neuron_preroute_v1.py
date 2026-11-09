"""Pack/place and export an RR graph from the frozen original Titan benchmark."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    start = time.perf_counter()
    frozen = R / 'experiments/titan23_neuron_transfer_freeze_v1_2026-10-13'
    p = frozen / 'verification.json'
    v = json.loads(p.read_text())
    assert v['archive_members_and_local_inputs_byte_identical']
    assert v['all_declared_models_and_buffered_architecture_switches_pass']
    assert all(sha(q) == h for q, h in v['bindings'].items())
    config = json.loads((frozen / 'protocol.json').read_text())
    out = R / 'experiments/titan23_neuron_preroute_v1_2026-10-13'
    out.mkdir()
    bindings = {**v['bindings'], str(p): sha(p), **closure([Path(__file__)])}
    for name in ['design.blif', 'design.sdc', 'architecture.xml']:
        shutil.copyfile(frozen / name, out / name)
        bindings[str(out / name)] = sha(out / name)
    native = config['native']
    common = [native['binary'], str(out / 'architecture.xml'), 'design.blif', '--sdc_file', 'design.sdc', '--route_chan_width', str(native['channel_width']), '--num_workers', str(native['workers']), '--seed', str(native['seed']), '--max_router_iterations', str(native['maximum_router_iterations'])]
    commands = [
        ('pack', common + ['--pack', '--net_file', 'design.net']),
        ('place', common + ['--place', '--net_file', 'design.net', '--place_file', 'design.place']),
        ('graph', common + ['--analysis', '--net_file', 'design.net', '--place_file', 'design.place', '--route_file', 'missing.route', '--write_rr_graph', 'rr_graph.xml', '--check_route', 'full']),
    ]
    protocol = dict(bindings=bindings, commands=commands, timeout_policy='No elapsed-time cancellation.', shared_state='Original TilePlace inputs and VTR source/binaries read-only. Every output is in this isolated RouteCast directory.', scope='Original Titan23/neuron mapped input, default Stratix IV architecture and original SDC. Pre-route placement/RR admission only. Native quality labels, RR electrical/endpoint/model acceptance and strict family holdout remain pending.')
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    env = {k: val for k, val in os.environ.items() if not k.startswith('ROUTECAST_')}
    env['OMP_NUM_THREADS'] = '1'
    rows = []
    for stage, command in commands:
        assert all(sha(q) == h for q, h in bindings.items())
        tick = time.perf_counter()
        print('TITAN PREROUTE START', stage, flush=True)
        with (out / (stage + '.log')).open('x') as log:
            process = subprocess.Popen(command, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
            (out / 'live_stage.json').write_text(json.dumps(dict(stage=stage, pid=process.pid, command=command, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()), indent=2) + '\n')
            status = process.wait()
        row = dict(stage=stage, exit_status=status, process_seconds=time.perf_counter() - tick, status='FAILED')
        text = (out / (stage + '.log')).read_text()
        expected = status == 0 and 'VPR succeeded' in text if stage != 'graph' else status == 1 and 'Completed placement consistency check successfully.' in text and 'Cannot open missing.route' in text and (out / 'rr_graph.xml').is_file()
        if expected and not list(out.glob('*.route')):
            row['status'] = 'PASS' if stage != 'graph' else 'EXPECTED_MISSING_ROUTE_AFTER_GRAPH_EXPORT'
        rows.append(row)
        (out / (stage + '_terminal.json')).write_text(json.dumps(row, indent=2) + '\n')
        (out / 'rows.json').write_text(json.dumps(rows, indent=2) + '\n')
        print('TITAN PREROUTE TERMINAL', json.dumps(row), flush=True)
        if row['status'] == 'FAILED':
            (out / 'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=status or 1, all_stages_completed=False, failed_stage=stage, source_inputs_unchanged=all(sha(q) == h for q, h in bindings.items())), indent=2) + '\n')
            raise SystemExit(status or 1)
        for name in ['design.net', 'design.place']:
            path = out / name
            if path.exists() and str(path) not in bindings:
                bindings[str(path)] = sha(path)
    assert all(sha(q) == h for q, h in bindings.items())
    for path in out.iterdir():
        if path.is_file():
            bindings[str(path)] = sha(path)
    (out / 'verification.json').write_text(json.dumps(dict(bindings=bindings, rows=rows, complete_native_pack_place_and_rr_export_pass=True, native_route_labels_generated=False, whole_driver_seconds=time.perf_counter() - start, scope=protocol['scope']), indent=2) + '\n')
    (out / 'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0, all_stages_completed=True)) + '\n')
    print('TITAN PREROUTE COMPLETE', flush=True)


if __name__ == '__main__':
    main()
