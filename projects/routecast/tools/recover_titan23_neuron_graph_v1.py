"""Authenticate the successful post-place snapshot and continue RR-only export."""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as E

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha, placements, extract
from source_binding_v2 import closure


def main():
    begin = time.perf_counter()
    old = R / 'experiments/titan23_neuron_preroute_v1_2026-10-13'
    pp = old / 'protocol.json'
    predecessor = json.loads(pp.read_text())
    assert all(sha(p) == h for p, h in predecessor['bindings'].items())
    rows = json.loads((old / 'rows.json').read_text())
    assert [r['stage'] for r in rows] == ['pack', 'place']
    assert all(r['exit_status'] == 0 and r['status'] == 'PASS' for r in rows)
    assert all('VPR succeeded' in (old / (s + '.log')).read_text() for s in ['pack', 'place'])
    failure_log = Path('/tmp/routecast_titan23_neuron_preroute.log')
    assert 'AssertionError' in failure_log.read_text()
    assert not (old / 'graph.log').exists() and not (old / 'rr_graph.xml').exists()
    net_hash = sha(old / 'design.net')
    locs = placements(old / 'design.place', net_hash)
    root = E.parse(old / 'design.net').getroot()
    assert root.get('architecture_id') == 'SHA256:' + sha(old / 'architecture.xml')
    assert root.get('atom_netlist_id') == 'SHA256:' + sha(old / 'design.blif')
    clusters = root.findall('block')
    assert set(locs) == {b.get('name') for b in clusters}
    assert len(locs) == len(clusters) == 3438
    out = R / 'experiments/titan23_neuron_graph_recovery_v1_2026-10-13'
    out.mkdir()
    work = out / 'neuron'
    work.mkdir()
    bindings = {**predecessor['bindings'], **closure([Path(__file__), R / 'tools/verify_freecores_rr_endpoints_v1.py']), str(pp): sha(pp)}
    for name in ['design.blif', 'design.sdc', 'architecture.xml', 'design.net', 'design.place']:
        shutil.copyfile(old / name, work / name)
        bindings[str(old / name)] = sha(old / name)
        bindings[str(work / name)] = sha(work / name)
    for name in ['rows.json', 'pack_terminal.json', 'place_terminal.json', 'pack.log', 'place.log']:
        bindings[str(old / name)] = sha(old / name)
    shutil.copyfile(failure_log, out / 'original_driver_failure.log')
    bindings[str(out / 'original_driver_failure.log')] = sha(out / 'original_driver_failure.log')
    frozen = R / 'experiments/titan23_neuron_transfer_freeze_v1_2026-10-13/protocol.json'
    native = json.loads(frozen.read_text())['native']
    cmd = [native['binary'], str(work / 'architecture.xml'), 'design.blif', '--sdc_file', 'design.sdc', '--analysis', '--net_file', 'design.net', '--place_file', 'design.place', '--route_file', 'missing.route', '--write_rr_graph', 'rr_graph.xml', '--route_chan_width', str(native['channel_width']), '--num_workers', '1', '--seed', str(native['seed']), '--max_router_iterations', str(native['maximum_router_iterations']), '--check_route', 'full']
    protocol = dict(bindings=bindings, command=cmd, recovery=dict(original_driver_terminal='AssertionError before graph stage; pack/place native processes both exit0.', original_protocol_bound_inputs_unchanged=True, limitation='Original driver did not persist the intermediate generated-file digests added in memory. The exact differing intermediate digest cannot be reconstructed from its log. No claim of pack-to-place byte immutability is made.', postplace_authentication='Packed architecture/atom input hashes and placement Netlist_ID match; all3438cluster names and unique legal coordinate slots match. Native placement consistency and RR-only reload are independently required.', original_failed_outputs_preserved=True, no_pack_or_place_restart=True), scope='Recovery from a successful native post-place snapshot with original architecture/SDC and new frozen intermediate digests. No route labels or predictor acceptance yet.')
    (out / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    tick = time.perf_counter()
    with (work / 'graph.log').open('x') as log:
        process = subprocess.Popen(cmd, cwd=work, env={k: v for k, v in os.environ.items() if not k.startswith('ROUTECAST_')}, stdout=log, stderr=subprocess.STDOUT)
        (out / 'live_stage.json').write_text(json.dumps(dict(stage='graph', pid=process.pid, command=cmd, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()), indent=2) + '\n')
        status = process.wait()
    (out / 'graph_terminal.json').write_text(json.dumps(dict(exit_status=status, process_seconds=time.perf_counter() - tick)) + '\n')
    text = (work / 'graph.log').read_text()
    assert status == 1 and 'Completed placement consistency check successfully.' in text and 'Cannot open missing.route' in text
    assert (work / 'rr_graph.xml').is_file() and not list(work.glob('*.route'))
    assert all(sha(p) == h for p, h in bindings.items())
    print('TITAN GRAPH EXPORT AND PLACEMENT RELOAD PASS', flush=True)
    try:
        tick = time.perf_counter()
        ep, mapping = extract(work / 'design.net', work / 'design.place', work / 'rr_graph.xml')
        (work / 'endpoints.json').write_text(json.dumps(ep) + '\n')
        (work / 'mapping.json').write_text(json.dumps(mapping) + '\n')
        row = dict(name='neuron', exit_code=status, status='GRAPH_AND_ENDPOINTS_CAPTURED', connections=len(ep['connections']), extraction_seconds=time.perf_counter() - tick, files={str(p): sha(p) for p in work.iterdir() if p.is_file()})
        receipt = out / 'receipt.json'
        receipt.write_text(json.dumps(dict(bindings=bindings, rows=[row], native_route_labels_generated=False), indent=2) + '\n')
        print('TITAN ENDPOINTS CAPTURED', len(ep['connections']), flush=True)
        with (out / 'endpoint_audit.log').open('x') as log:
            code = subprocess.call([sys.executable, str(R / 'tools/verify_freecores_rr_endpoints_v1.py'), str(work), str(receipt)], cwd=R, stdout=log, stderr=subprocess.STDOUT)
        (out / 'endpoint_audit_terminal.json').write_text(json.dumps(dict(exit_status=code)) + '\n')
        assert code == 0
    except Exception as exc:
        (out / 'endpoint_failure.json').write_text(json.dumps(dict(error=repr(exc), graph_export_and_native_placement_check_pass=True, no_route_labels=True, elapsed_seconds=time.perf_counter() - begin), indent=2) + '\n')
        raise
    assert all(sha(p) == h for p, h in bindings.items())
    for path in out.rglob('*'):
        if path.is_file():
            bindings[str(path)] = sha(path)
    (out / 'verification.json').write_text(json.dumps(dict(bindings=bindings, postplace_identity_native_consistency_RR_and_endpoint_audit_pass=True, connections=len(ep['connections']), all_original_inputs_unchanged=True, native_route_labels_generated=False, strict_unseen_family_certified=False, whole_recovery_seconds=time.perf_counter() - begin, scope=protocol['scope']), indent=2) + '\n')
    print('TITAN RECOVERY ENDPOINT ADMISSION COMPLETE', flush=True)


if __name__ == '__main__':
    main()
