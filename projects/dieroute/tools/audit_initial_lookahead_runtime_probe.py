"""Review the bounded observational relink and all initial MAP queries."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'work/initial_lookahead_runtime_probe_20261018'
PARENT = ROOT / 'work/vpr_source_bound_initial_observation_build_20261015'

def main():
    refs = {}
    def sha(p):
        p = Path(p)
        value = hashlib.sha256(p.read_bytes()).hexdigest()
        refs[str(p)] = value
        return value
    def read(p):
        sha(p)
        return json.loads(Path(p).read_text())
    build = read(PROBE / 'manifest.json')
    assert build['status'] == 'observational_binary_built_requires_dependency_and_native_equivalence_review'
    assert sha(build['executable']) == build['executable_sha256']
    protocol = read(PROBE / 'protocol.json')
    for group in ['parent_inputs_sha256', 'patched_source_sha256']:
        for name, expected in protocol[group].items():
            assert sha(name) == expected, name
    assert sha(PROBE / 'build_probe.py') == protocol['driver_sha256']
    dependencies = read(PROBE / 'compiled_dependency_review.json')
    for name, expected in dependencies['source_sha256'].items():
        assert sha(name) == expected, name
    for name in ['route_net.cpp.o', 'router_lookahead_map.cpp.o']:
        member = subprocess.check_output(['/usr/bin/ar', 'p', str(PROBE / 'libvpr.a'), name])
        assert hashlib.sha256(member).hexdigest() == sha(PROBE / name)
    sha(PROBE / 'libvpr.a')
    receipt = read(PROBE / 'run_receipt.json')
    assert receipt['status'] == 'terminal_requires_independent_review' and receipt['returncode'] == 0
    current = PROBE / 'native_probe'
    parent = PARENT / 'native_repeat_0'
    records = [read(d / 'run.json') for d in [parent, current]]
    for directory, record in zip([parent, current], records):
        assert record['status'] == 'passed' and record['returncode'] == 0
        for name, meta in record['artifacts'].items():
            assert sha(directory / name) == meta['sha256'], name
    assert records[0]['command'][1:] == records[1]['command'][1:]
    assert records[1]['sources']['vpr']['sha256'] == build['executable_sha256']
    for kind in ['arch', 'circuit']:
        assert records[0]['sources'][kind]['sha256'] == records[1]['sources'][kind]['sha256']
    canonical = ['circuit.net', 'circuit.net.post_routing', 'circuit.place', 'circuit.route', 'rr_graph.xml']
    for name in canonical:
        assert sha(parent / name) == sha(current / name), name
    text = (current / 'vpr.log').read_text()
    assert 'RouterOpts.check_route: FULL' in text
    assert 'Circuit successfully routed with a channel width factor of 80.' in text
    wl = int(re.findall(r'Total wirelength:\s+(\d+)', text)[-1])
    cpd = float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns', text)[-1])
    assert (wl, cpd) == (9664, 9.60037)
    assert sha(PROBE / 'initial_timing.csv') == sha(PARENT / 'initial_timing_0.csv')
    observations = list(csv.DictReader((PROBE / 'initial_timing.csv').open()))
    queries = list(csv.DictReader((PROBE / 'map_queries.csv').open()))
    assert len(observations) == 1920 and len(queries) == 3840
    graph = ET.parse(current / 'rr_graph.xml').getroot()
    nodes = {int(n.attrib['id']): n for n in graph.find('rr_nodes')}
    cross_target = 0
    for i, observation in enumerate(observations):
        pair = queries[2*i:2*i+2]
        assert [int(v['via_layer']) for v in pair] == [0, 1]
        for query in pair:
            assert all(query[k] == observation[k] for k in ['source_rr', 'sink_rr'])
        zeros = [q for q in pair if float(q['delay_cost']) == 0]
        assert len(zeros) == 1
        zero = zeros[0]
        assert int(zero['direct_count']) == 1 and float(zero['direct_min_delay']) == 0
        source_layer = int(nodes[int(observation['source_rr'])].find('loc').attrib['layer'])
        target_layer = int(nodes[int(observation['sink_rr'])].find('loc').attrib['layer'])
        assert int(zero['via_layer']) == source_layer
        assert all(int(q['target_layer']) == target_layer for q in pair)
        assert float(observation['lookahead_delay_s']) == min(float(q['delay_cost']) for q in pair) == 0
        cross_target += source_layer != target_layer
    sha(PROBE / 'map_queries.csv')
    for p in [PROBE / 'link.log', PROBE / 'native_wrapper.log', Path(__file__).resolve(),
              PARENT / 'source_vtr/vpr/src/route/router_lookahead_map_utils.cpp']:
        sha(p)
    result = {'status': 'all_1920_initial_queries_zero_direct_candidate_and_native_identity_reviewed',
              'connections': 1920, 'layer_candidates': 3840, 'cross_layer_target_connections': cross_target,
              'zero_direct_candidate_connections': 1920, 'native_wirelength': wl, 'native_cpd_ns': cpd,
              'byte_equal_canonical_outputs': canonical, 'initial_csv_byte_equal': True,
              'source_sha256': refs,
              'interpretation': 'At criticality 1, MAP considers a same-source-layer zero-delay direct SINK candidate for every observed connection, including cross-layer targets. Its minimum delay is zero and congestion is multiplied by zero. The direct-candidate helper does not condition its SINK shortcut on the queried target identity or displacement. This explains the observed initial zeros for this run.',
              'scope': 'One ex5p seed1 native full-route observation, relinking two observational units with archived parent libraries. Not universal behavior, zero physical delay, corrected/calibrated estimates, a clean full-source rebuild, policy adoption or hardware acceleration.',
              'research_complete': False, 'board_result': False}
    with (PROBE / 'independent_audit.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ['status', 'connections', 'cross_layer_target_connections', 'native_wirelength', 'native_cpd_ns']}))

if __name__ == '__main__':
    main()
