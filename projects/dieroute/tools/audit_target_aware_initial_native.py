"""Audit all five frozen initial-only development attempts, including regressions."""
import csv
import hashlib
import heapq
import json
import math
from pathlib import Path
import re
import shlex
import struct
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'work/initial_lookahead_target_aware_variant_20261018'
PARENT = ROOT / 'work/vpr_source_bound_initial_observation_build_20261015'

def main():
    refs = {}
    def sha(p):
        p = Path(p)
        result = hashlib.sha256(p.read_bytes()).hexdigest()
        refs[str(p)] = result
        return result
    def read(p):
        sha(p)
        return json.loads(Path(p).read_text())
    queue = read(HERE / 'native_queue.json')
    assert queue['status'] == 'all_five_attempts_terminal_requires_independent_review'
    assert len(queue['attempts']) == 5
    # No failed attempt may silently disappear from the denominator.
    assert all(a['returncode'] == 0 for a in queue['attempts']), 'Classify failed attempts before success claims'
    protocol = read(HERE / 'protocol.json')
    build = read(HERE / 'build_protocol.json')
    for name, expected in {**protocol['source_sha256'], **build['parent_inputs_sha256'], **build['patched_source_sha256']}.items():
        assert sha(name) == expected, name
    assert sha(HERE / 'build_variant.py') == build['driver_sha256']
    receipt = read(HERE / 'native_launch_receipt.json')
    assert sha(HERE / 'run_five_native.py') == receipt['driver_sha256']
    assert sha(HERE / 'protocol.json') == receipt['protocol_sha256']
    manifest = read(HERE / 'manifest.json')
    binary = Path(manifest['executable'])
    assert sha(binary) == manifest['executable_sha256']
    for dep in HERE.glob('*.cpp.d'):
        sha(dep)
        words = shlex.split(dep.read_text().replace('\\\n', ' ').split(':', 1)[1])
        for word in words:
            sha(Path(word))
        obj = HERE / (dep.name[:-2] + '.o')
        member = subprocess.check_output(['/usr/bin/ar', 'p', str(HERE / 'libvpr.a'), obj.name])
        assert hashlib.sha256(member).hexdigest() == sha(obj)
    sha(HERE / 'libvpr.a')
    parent = PARENT / 'native_repeat_0'
    original = read(parent / 'run.json')
    initial_parent = list(csv.DictReader((PARENT / 'initial_timing_0.csv').open()))
    sha(PARENT / 'initial_timing_0.csv')
    graph = ET.parse(parent / 'rr_graph.xml').getroot()
    sha(parent / 'rr_graph.xml')
    types = {int(n.attrib['id']): n.attrib['type'] for n in graph.find('rr_nodes')}
    f32 = lambda x: struct.unpack('f', struct.pack('f', x))[0]
    switches = {int(s.attrib['id']): f32(float(s.find('timing').attrib.get('Tdel', 0))) for s in graph.find('switches')}
    adjacent = {}
    for edge in graph.find('rr_edges'):
        a = edge.attrib
        u, v, sw = (int(a[k]) for k in ['src_node', 'sink_node', 'switch_id'])
        if types[u] in ['SOURCE', 'OPIN', 'IPIN'] and types[v] in ['SOURCE', 'OPIN', 'IPIN', 'SINK']:
            assert math.isfinite(switches[sw]) and switches[sw] >= 0
            adjacent.setdefault(u, []).append((v, switches[sw]))
    cache = {}
    def direct_oracle(source, target):
        if source not in cache:
            costs = {source: 0.0}
            pending = [(0.0, source)]
            while pending:
                cost, u = heapq.heappop(pending)
                if cost != costs[u] or types[u] == 'SINK':
                    continue
                for v, delay in adjacent.get(u, []):
                    candidate = f32(cost + delay)
                    if candidate < costs.get(v, math.inf):
                        costs[v] = candidate
                        heapq.heappush(pending, (candidate, v))
            cache[source] = costs
        return cache[source].get(target, math.inf)
    baseline = None
    rows = []
    for attempt in queue['attempts']:
        i = attempt['index']
        directory = HERE / f'native_repeat_{i}'
        record = read(directory / 'run.json')
        assert record['status'] == 'passed' and record['returncode'] == 0
        assert record['sources']['vpr']['sha256'] == manifest['executable_sha256']
        assert record['command'][1:] == original['command'][1:]
        for kind in ['arch', 'circuit']:
            assert record['sources'][kind]['sha256'] == original['sources'][kind]['sha256']
        for name, info in record['artifacts'].items():
            assert sha(directory / name) == info['sha256'], name
        # Inputs to routing must remain equal; outputs may legitimately change.
        for name in ['circuit.net', 'circuit.place', 'rr_graph.xml']:
            assert sha(directory / name) == sha(parent / name), name
        canonical = {name: sha(directory / name) for name in ['circuit.net', 'circuit.net.post_routing', 'circuit.place', 'circuit.route', 'rr_graph.xml']}
        initial_path, query_path = HERE / f'initial_timing_{i}.csv', HERE / f'queries_{i}.csv'
        canonical['initial_csv'] = sha(initial_path)
        canonical['query_csv'] = sha(query_path)
        if baseline is None:
            baseline = canonical
        assert canonical == baseline, 'Candidate repeats differ'
        initial = list(csv.DictReader(initial_path.open()))
        queries = list(csv.DictReader(query_path.open()))
        assert len(initial) == len(queries) == len(initial_parent) == 1920
        for old, observation, query in zip(initial_parent, initial, queries):
            for key in ['net_id', 'net_pin_index', 'source_rr', 'sink_rr', 'is_clock', 'max_criticality', 'criticality_exp']:
                assert old[key] == observation[key]
            assert all(query[k] == observation[k] for k in ['source_rr', 'sink_rr'])
            exact = direct_oracle(int(query['source_rr']), int(query['sink_rr']))
            assert float(query['exact_direct_delay']) == exact
            expected = min(float(query['wire_min_delay']), exact)
            assert float(query['selected_delay']) == float(observation['lookahead_delay_s']) == expected
            assert math.isfinite(expected) and expected >= 0
            if expected == 0:
                assert exact == 0, 'Unexplained zero wire estimate'
        text = (directory / 'vpr.log').read_text()
        assert 'RouterOpts.check_route: FULL' in text
        assert 'Circuit successfully routed with a channel width factor of 80.' in text
        wl = int(re.findall(r'Total wirelength:\s+(\d+)', text)[-1])
        cpd = float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns', text)[-1])
        rows.append({'repeat': i, 'wirelength': wl, 'cpd_ns': cpd,
                     'wirelength_change_percent': 100*(wl/9664-1), 'cpd_change_percent': 100*(cpd/9.60037-1),
                     'zero_initial_delays': sum(float(v['lookahead_delay_s']) == 0 for v in initial),
                     'changed_initial_criticalities': sum(v['route_criticality'] != old['route_criticality'] for v, old in zip(initial, initial_parent)),
                     'joint_parent_quality_pass': wl <= 9664 and cpd <= 9.60037})
    for p in [Path(__file__).resolve(), HERE / 'driver_lineage.json', HERE / 'link.log', HERE / 'component_audit.json']:
        sha(p)
    result = {'status': 'five_initial_only_target_aware_native_attempts_and_direct_oracle_reviewed',
              'attempts': 5, 'successful_attempts': 5, 'rows': rows,
              'exact_direct_query_comparisons': 9600, 'candidate_repeat_artifacts_equal': True,
              'source_sha256': refs,
              'scope': 'One development ex5p seed, five repetitions. Exact direct terminal and switch-Tdel oracle checked; wire-map estimates remain heuristic, not calibrated RC timing. Initial-only policy changes; inherited build status uses legacy observational wording, but this experiment is a semantic correction, not output equivalence to the parent. Ordinary-route lookup policy retained. Shared-host times are not a performance study. All quality regressions retained; no adoption, heldout guarantee or hardware claim.',
              'adopted': False, 'research_complete': False, 'board_result': False}
    with (HERE / 'independent_audit.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({'status': result['status'], 'rows': rows}))

if __name__ == '__main__':
    main()
