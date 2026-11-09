"""Current-host fixed-placement no-feedback native routing development baseline."""
import datetime
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

from pre_route_endpoints import sha


def run():
    root = Path(__file__).resolve().parents[1]
    front = root / 'experiments/conv_layer_global_frontend_v2_2026-10-06'
    fp = json.loads((front / 'protocol.json').read_text())
    fr = json.loads((front / 'receipt.json').read_text())
    assert fr['protocol_sha256'] == sha(front / 'protocol.json')
    inputs = fp['inputs']
    assert all(sha(v['path']) == v['sha256'] for v in inputs.values())
    vpr = root.parent / 'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr'
    out = root / 'experiments/conv_layer_current_host_no_sketch_native_2026-10-06'
    work = root / 'work/conv_layer_current_host_no_sketch_native_2026-10-06'
    out.mkdir()
    work.mkdir(parents=True)
    binary_sha = sha(vpr)
    shutil.copy2(vpr, out / 'vpr')
    assert sha(out / 'vpr') == binary_sha == sha(vpr)
    for key, name in (('atom', 'conv_layer.pre-vpr.blif'),
                      ('packed_netlist', 'conv_layer.pre-vpr.net'),
                      ('reference_place', 'conv_layer.pre-vpr.place')):
        shutil.copyfile(inputs[key]['path'], work / name)
        assert sha(work / name) == inputs[key]['sha256']
    command = [str(out / 'vpr'), inputs['architecture']['path'], 'conv_layer.pre-vpr.blif',
               '--route', '--net_file', 'conv_layer.pre-vpr.net',
               '--place_file', 'conv_layer.pre-vpr.place', '--route_file', 'design.route',
               '--read_rr_graph', inputs['rr_graph']['path'], '--route_chan_width', '300',
               '--num_workers', '1', '--seed', '1', '--max_router_iterations', '100',
               '--timing_report_npaths', '10']
    protocol = {'inputs': inputs, 'frontend_receipt_sha256': sha(front / 'receipt.json'),
                'vpr_original': str(vpr), 'frozen_vpr_sha256': binary_sha,
                'command': command, 'cwd': str(work), 'timeout_s': 600,
                'host': {'uname': platform.uname()._asdict(), 'affinity': sorted(os.sched_getaffinity(0))},
                'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_sha256': sha(__file__),
                'scope': 'current host route-only, fixed frozen packed netlist/place/RR graph, one worker, no sketch or feedback; tool is current archived VTR build, historical VPR9 binary equivalence not asserted'}
    shutil.copyfile(__file__, out / 'source.py')
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps({'stage': 'native_route_started', 'protocol_sha256': sha(out / 'protocol.json')}), flush=True)
    start = time.monotonic()
    with (out / 'stdout.log').open('wb') as log:
        try:
            result = subprocess.run(command, cwd=work, stdout=log, stderr=subprocess.STDOUT, timeout=600)
            code, timed_out = result.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    elapsed = time.monotonic() - start
    route = work / 'design.route'
    unchanged = all(sha(v['path']) == v['sha256'] for v in inputs.values())
    log_text = (out / 'stdout.log').read_text(errors='replace')
    receipt = {'exit_code': code, 'timed_out': timed_out, 'wall_s': elapsed,
               'protocol_sha256': sha(out / 'protocol.json'),
               'stdout_sha256': sha(out / 'stdout.log'),
               'route_sha256': sha(route) if route.exists() else None,
               'routing_success_reported': 'Circuit successfully routed with a channel width factor of 300.' in log_text and 'Completed routing consistency check successfully.' in log_text and 'VPR succeeded' in log_text,
               'original_inputs_unchanged': unchanged,
               'frozen_binary_unchanged': sha(out / 'vpr') == binary_sha,
               'scope': protocol['scope']}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)
    assert unchanged and receipt['frozen_binary_unchanged']
    assert code == 0 and route.exists() and receipt['routing_success_reported'], 'inspect archived native failure; no restart'


if __name__ == '__main__':
    run()
