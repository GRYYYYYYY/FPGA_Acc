"""Full original neuron native label audit; stages preserve failures independently."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import re
import resource
import sys
import time
import traceback
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_NET_occupancy_v1 import NET, occupancy
from stream_native_route_audit_expat_v4 import audit
from rooted_canonical_native_reload_v2 import reload
from native_route_work_metrics_v2 import extract
from neuron_complete_prediction_metrics_v1 import evaluate

N = R / 'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
O = R / 'experiments/titan23_neuron_native_label_audit_v2_2026-10-15'
M = R / 'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13/model'
E = R / 'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
PR = R / 'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json'


def load(p):
    return json.loads(p.read_text())


def write(p, data):
    with p.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')


def checked(bindings):
    for p, expected in bindings.items():
        assert sha(p) == expected, ('changed input', p)


def physical():
    O.mkdir(exist_ok=False)
    launch, terminal = load(N / 'launch.json'), load(N / 'terminal.json')
    assert terminal['exit_status'] == 0 and load(N / 'input_postcheck.json')['all_inputs_unchanged']
    assert sha(PR) == launch['prereg_sha256']
    bindings = dict(closure([Path(__file__)]))
    for group in load(N / 'input_bindings.json').values():
        for p, h in group.items():
            assert p not in bindings or bindings[p] == h
            bindings[p] = h
    for p in [E, PR, N / 'launch.json', N / 'terminal.json', N / 'input_postcheck.json',
              N / 'output.route', N / 'native.log', N / 'design.net.post_routing']:
        bindings[str(p)] = sha(p)
    checked(bindings)
    ep = load(E)
    graph = Path(ep['inputs']['graph']['path'])
    assert sha(graph) == ep['graph_sha256']
    result = audit(graph, N / 'output.route')
    names = {}
    for line in (N / 'output.route').open():
        m = NET.match(line)
        if m:
            assert int(m[1]) not in names
            names[int(m[1])] = m[2]
    assert len(set(names.values())) == len(names)
    identity = [json.loads(line) for line in Path(ep['inputs']['native_identity']['path']).open()]
    assert set(names.values()) == {row['name'] for row in identity}
    required = Counter((ep['net_names'][str(q['net_id'])], q['source'], q['sink'])
                       for q in ep['connections'])
    observed = Counter((names[q['net_id']], q['source'], q['sink']) for q in result['connections'])
    assert required == observed, ('complete demand mismatch', len(required - observed), len(observed - required))
    assert sum(required.values()) == 77106 and result['routed_nets'] == 50767
    assert result['overflow_units'] == 0
    counted, count_nets = occupancy(N / 'output.route')
    assert counted == result['node_occupancy'] and count_nets == len(names)
    write(O / 'physical_audit.json', result)
    log = (N / 'native.log').read_text()
    assert 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log
    work = extract(log)
    assert work['routing_success'] and work['iterations'] == 18
    qor = dict(cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)', log)[-1]),
               wirelength=int(re.findall(r'Total wirelength:\s*(\d+)', log)[-1]),
               native_process_seconds=terminal['seconds'], native_peak_rss_kib=terminal['sampled_peak_rss_kib'],
               **work)
    bindings[str(O / 'physical_audit.json')] = sha(O / 'physical_audit.json')
    checked(bindings)
    write(O / 'physical_verification.json', dict(bindings=bindings, complete_native_demand_pass=True,
          original_XML_arcs_switches_branches_and_unique_NET_capacity_pass=True,
          independent_streamed_occupancy_parity_pass=True, connections=77106, routed_nets=50767,
          all_NET_headers=count_nets, overflow_units=0, native_qor=qor, label_accepted=False,
          canonical_and_ignored_pin_audit_pending=True))
    print('PHYSICAL PASS', 77106, 'connections', 50767, 'routed NETs', flush=True)


def canonical():
    proof = load(O / 'physical_verification.json')
    assert proof['complete_native_demand_pass']
    checked(proof['bindings'])
    # Lower than the cold run's 24 GiB cap; original observed RSS was 7.26 GiB.
    child_limit = 16 * 2**30
    current = int(Path('/sys/fs/cgroup/memory.current').read_text())
    maximum = int(Path('/sys/fs/cgroup/memory.max').read_text())
    admission = dict(current_bytes=current, maximum_bytes=maximum,
                     child_address_space_limit_bytes=child_limit, margin_bytes=8 * 2**30)
    assert maximum - current >= child_limit + admission['margin_bytes'], admission
    write(O / 'canonical_memory_admission.json', admission)
    candidate = dict(command=load(N / 'launch.json')['command'], cpd_ns=proof['native_qor']['cpd_ns'],
                     files={str(p): sha(p) for p in N.iterdir() if p.is_file()})
    identity = R / 'build/native_ignored_identity_v1_2026-10-08/routecast_net_identity_vpr'
    binary = R / 'build/native_verbose_sync_v2_2026-10-08/verbose_sync_vpr'
    bindings = {**closure([Path(__file__)]), **proof['bindings'],
                str(O / 'physical_verification.json'): sha(O / 'physical_verification.json'),
                str(identity): sha(identity), str(binary): sha(binary)}
    result = reload(candidate, N, O / 'canonical', identity, binary, child_memory_bytes=child_limit)
    assert result['semantic_consistency_gate_pass'] and result['explicit_SDC_preserved']
    checked(bindings)
    write(O / 'canonical_receipt.json', dict(bindings=bindings, result=result))
    print('CANONICAL FULL/STA PASS', result['cpd_ns'], flush=True)


def ignored():
    receipt = load(O / 'canonical_receipt.json')
    checked(receipt['bindings'])
    checked(receipt['result']['files'])
    d = O / 'canonical'
    records = [json.loads(line) for line in (d / 'identity.jsonl').open()]
    ep = load(E)
    original = [json.loads(line) for line in Path(ep['inputs']['native_identity']['path']).open()]
    assert {(r['name'], r['ignored']) for r in original} == {(r['name'], r['ignored']) for r in records}
    expected = Counter((r['name'], p['block'], p['x'], p['y'], p['layer'], p['port'], p['bit'])
                       for r in records if r['ignored'] for p in r['pins'] if p['index'] > 0)
    pattern = re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)")
    observed = Counter()
    for m in pattern.finditer((d / 'reload.log').read_text()):
        routed, block, x, y, tile, port, bit, layer, old = m.groups()
        assert routed == 'unmapped'
        observed[old, block, int(x), int(y), int(layer), port, int(bit)] += 1
    assert not observed - expected
    assert sum(observed.values()) == receipt['result']['native_ignored_only_mismatch_pins']
    untouched = expected - observed
    blocks = {b.get('name'): b for b in ET.parse(d / 'design.net').getroot().findall('block')}
    for (net, block, x, y, layer, port, bit), count in untouched.items():
        assert count == 1 and block in blocks
        ports = [p for section in ['inputs', 'outputs', 'clocks'] for p in blocks[block].findall(section + '/port')
                 if p.get('name') == port]
        assert len(ports) == 1 and (ports[0].text or '').split()[bit] == net
    assert sha(d / 'design.net') == sha(d / 'design.net.post_routing')
    checked(receipt['bindings'])
    checked(receipt['result']['files'])
    write(O / 'label_verification.json', dict(bindings={str(O / 'canonical_receipt.json'): sha(O / 'canonical_receipt.json'),
          str(O / 'physical_verification.json'): sha(O / 'physical_verification.json'), **closure([Path(__file__)])},
          original_all_NET_ignored_flags_identical=True, all_ignored_pin_occurrences=sum(expected.values()),
          matched_ignored_only_repairs=sum(observed.values()), untouched_correct_ignored_pins=sum(untouched.values()),
          packed_netlist_byte_identical=True, independent_original_XML_complete_demand_and_capacity_pass=True,
          canonical_original_FULL_and_STA_and_ignored_pin_semantics_pass=True, label_accepted=True,
          heldout_family_certified=False, scope='Original frozen neuron cold label, complete development case. No end-to-end benefit or heldout claim.'))
    print('LABEL ACCEPTED; ignored pins', sum(expected.values()), flush=True)


def metrics():
    proof = load(O / 'label_verification.json')
    assert proof['label_accepted']
    checked(proof['bindings'])
    physical_proof = load(O / 'physical_verification.json')
    checked(physical_proof['bindings'])
    canonical_proof = load(O / 'canonical_receipt.json')
    checked(canonical_proof['bindings']); checked(canonical_proof['result']['files'])
    frames = []
    for name in ['initial', 'sketch']:
        frame = load(M / (name + '.json'))
        assert frame['completed_connections'] == frame['required_connections'] == 77106
        frames.append(frame['ledger'])
        del frame
    gc.collect()
    native = load(O / 'physical_audit.json')['node_occupancy']
    graph = Path(load(E)['inputs']['graph']['path'])
    result = evaluate(graph, frames[0], frames[1], native)
    bindings = {**closure([Path(__file__)]), str(O / 'label_verification.json'): sha(O / 'label_verification.json'),
                str(graph): sha(graph), **{str(M / (n + '.json')): sha(M / (n + '.json')) for n in ['initial', 'sketch']}}
    result.update(bindings=bindings, native_qor=physical_proof['native_qor'])
    checked(bindings)
    write(O / 'prediction_metrics.json', result)
    print(json.dumps(result['metrics'], indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['physical', 'canonical', 'ignored', 'metrics'])
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (8 * 2**30, 24 * 2**30))
    tick = time.perf_counter()
    try:
        globals()[args.stage]()
    except BaseException:
        if O.exists():
            write(O / (args.stage + '_failure.json'), dict(traceback=traceback.format_exc(),
                  seconds=time.perf_counter() - tick, utc=datetime.now(timezone.utc).isoformat()))
        raise
    write(O / (args.stage + '_terminal.json'), dict(exit_status=0, seconds=time.perf_counter() - tick,
          peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    main()
