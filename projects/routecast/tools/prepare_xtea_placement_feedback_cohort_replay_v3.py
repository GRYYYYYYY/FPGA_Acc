"""Freeze eight geometry-selected moves for a prospective SKETCH on/off shell."""
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from collections import defaultdict

R = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(R / 'tools'), str(R / 'tools/native_resume_prototype')]
from pre_route_endpoints import sha, placements, physical_maps, extract
from source_binding_v2 import closure
from prepare_live_native_manifest_v2 import prepare


def main():
    begin = time.perf_counter()
    out = Path(sys.argv[1]).resolve()
    out.mkdir()
    src = R / 'experiments/freecores_rr_only_v1_2026-10-08/xtea'
    old = R / 'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
    graph = src / 'rr_graph.xml'
    arch = R / 'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
    binary = R / 'build/native_candidate_retained_search_2026-10-06/sequence_vpr'
    scripts = [R / 'tools' / name for name in [
        'verify_freecores_rr_endpoints_v1.py',
        'prepare_native_demand_no_timeout_v1.py',
        'verify_freecores_native_demand_v1.py',
    ]]
    bindings = closure([Path(__file__), *scripts])
    for p in [old, arch, binary, *[src / n for n in ['design.net', 'design.place', 'design.blif', 'rr_graph.xml', 'endpoints.json', 'mapping.json']]]:
        bindings[str(p)] = sha(p)
    ep = json.loads(old.read_text())
    assert all(sha(v['path']) == v['sha256'] for v in ep['inputs'].values())
    bindings.update({v['path']: v['sha256'] for v in ep['inputs'].values()})
    baseline = placements(src / 'design.place', sha(src / 'design.net'))
    types, grid, _ = physical_maps(graph)
    mapping = json.loads((src / 'mapping.json').read_text())
    nets, touches = defaultdict(set), defaultdict(set)
    included = {q['net_id'] for q in ep['connections']}
    for pin in mapping['pin_details']:
        if pin['net_id'] in included:
            nets[pin['net_id']].add(pin['block'])
            touches[pin['block']].add(pin['net_id'])

    def hpwl(pos, ids):
        total = 0
        for net in ids:
            xy = [pos[name][:2] for name in nets[net]]
            total += max(p[0] for p in xy) - min(p[0] for p in xy)
            total += max(p[1] for p in xy) - min(p[1] for p in xy)
        return total

    blocks = []
    for name, pos in sorted(baseline.items(), key=lambda item: item[1][4]):
        x, y, z, layer, bid = pos
        tid, wo, ho = grid[x, y, layer]
        if types[tid]['name'] == 'clb' and (wo, ho) == (0, 0) and (types[tid]['width'], types[tid]['height']) == (1, 1):
            blocks.append((name, (tid, z, layer)))
    excluded_file = R / 'experiments/xtea_legal_swap_endpoints_v1_2026-10-13/protocol.json'
    bindings[str(excluded_file)] = sha(excluded_file)
    excluded = {item[0] for item in json.loads(excluded_file.read_text())['selected']}
    total_hpwl = hpwl(baseline, nets)
    selected = []
    examined = 0
    for (a, ac), (b, bc) in itertools.combinations(blocks, 2):
        if ac != bc or {a, b} == excluded:
            continue
        examined += 1
        changed = {**baseline, a: (*baseline[b][:4], baseline[a][4]), b: (*baseline[a][:4], baseline[b][4])}
        affected = touches[a] | touches[b]
        delta = hpwl(changed, affected) - hpwl(baseline, affected)
        if delta <= 0:
            assert hpwl(changed, nets) == total_hpwl + delta
            selected.append(dict(candidate_id=len(selected) + 1, pair=[a, b], block_ids=[baseline[a][4], baseline[b][4]], hpwl=total_hpwl + delta, hpwl_delta=delta))
            if len(selected) == 8:
                break
    assert len(selected) == 8
    protocol = dict(
        bindings=bindings, baseline_endpoint=str(old), baseline_hpwl=total_hpwl,
        selected=selected, compatible_pairs_examined=examined,
        candidate_generation='First eight compatible unit-CLB swaps with nonpositive physical-demand endpoint-NET HPWL delta in ascending block-ID pair order; exclude the previously studied pair. Each starts from the same original placement.',
        placement_shell={
            'off': 'Select minimum (HPWL, candidate_id) from baseline0 and all eight candidates.',
            'on': 'Use the certified original retained sketch as baseline. Evaluate each independent candidate using the same fixed pre-move timing epoch, inherited history, exact moved wholeNET/sharedSOURCE closure, and two local retained-tree rounds. Admit a candidate only if sketch overflow <= baseline sketch overflow; select minimum (HPWL, candidate_id) among admitted candidates and baseline0.',
            'native': 'After freezing both decisions, run fresh cold native routing for baseline and each unique selected placement with identical binary, width128, worker1, seed1, max_iterations100. No sketch seed is imported in either arm.',
            'acceptance': 'Identical final gate in both arms: FULL physical/canonical legality, wirelength strictly below baseline and printed diagnostic CPD <= baseline. Otherwise retain baseline placement. Native results never rank alternative candidates.',
            'failure': 'Preserve any failed candidate and its terminal evidence; do not replace or drop it. Stop the trial for investigation before selection if mandatory model/physical checks fail.',
            'state': 'All candidate evaluations are staged independently against baseline; only the selected and native-accepted placement can become the next committed epoch.',
        },
        timing_policy='Freeze the original pre-move native timing epoch by stable pin identity; no post-move STA is fed into candidate selection.',
        cost_policy='Report common candidate/frontend preparation, previous-sketch construction, per-candidate endpoint/epoch/warm preparation, model, decisions, selected native and final gate separately, plus fresh driver total when executed. Archive/independent audits separately identified; reused original frontend costs remain explicit. No cost omission may be called end-to-end acceleration.',
        scope='Prospective development placement-decision experiment on exposed XTEA, not heldout-family validation or integration with live TilePlace. Earlier single-swap outcomes informed the mechanism; new candidate native outcomes are unavailable during this freeze. Async CPD remains diagnostic.',
        timeout_policy='No elapsed-time cancellation of launched jobs.',
    )
    predecessor = R / 'experiments/xtea_placement_feedback_cohort_v1_2026-10-13/protocol.json'
    original = json.loads(predecessor.read_text())
    for field in ['baseline_endpoint', 'baseline_hpwl', 'selected', 'compatible_pairs_examined', 'candidate_generation', 'placement_shell', 'timing_policy', 'cost_policy', 'scope', 'timeout_policy']:
        assert protocol[field] == original[field], field
    assert all(sha(p) == h for p, h in original['bindings'].items())
    bindings[str(predecessor)] = sha(predecessor)
    original_source = R / 'tools/prepare_xtea_placement_feedback_cohort_v1.py'
    bindings[str(original_source)] = sha(original_source)
    protocol['replay_scope'] = 'Fresh preparation of previously exposed frozen candidates;not prospective or unseen. No native route outcomes consumed in generation.'
    protocol['recovery'] = dict(original_protocol=str(predecessor), reason='Missing original-endpoint argv in native-demand auditor call; first two stages passed, stage2 IndexError. Original failed output retained; exact candidate, decision, timing and acceptance rules preserved; fresh v2 preparation measured separately.')
    protocol_path = out / 'protocol.json'
    protocol_path.write_text(json.dumps(protocol, indent=2) + '\n')
    protocol_digest = sha(protocol_path)
    print('FROZEN', total_hpwl, [(r['candidate_id'], r['block_ids'], r['hpwl_delta']) for r in selected], flush=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith('ROUTECAST_')}
    rows = []
    for item in selected:
        tick = time.perf_counter()
        directory = out / ('candidate_%02d' % item['candidate_id'])
        directory.mkdir()
        physical = directory / 'xtea'
        physical.mkdir()
        for name in ['design.net', 'design.blif']:
            shutil.copyfile(src / name, physical / name)
        (physical / 'rr_graph.xml').symlink_to(graph)
        a, b = item['pair']
        change = {a: baseline[b][:4], b: baseline[a][:4]}
        lines = []
        for line in (src / 'design.place').read_text().splitlines():
            fields = line.split()
            if fields and fields[0] in change:
                fields[1:5] = map(str, change[fields[0]])
                line = '\t'.join(fields)
            lines.append(line)
        (physical / 'design.place').write_text('\n'.join(lines) + '\n')
        pos = placements(physical / 'design.place', sha(physical / 'design.net'))
        assert {n for n in pos if pos[n] != baseline[n]} == {a, b}
        assert {p[:4] for p in pos.values()} == {p[:4] for p in baseline.values()}
        assert all(pos[n][4] == baseline[n][4] for n in pos)
        assert hpwl(pos, nets) == item['hpwl']
        command = [str(binary), str(arch), 'design.blif', '--analysis', '--net_file', 'design.net', '--place_file', 'design.place', '--route_file', 'missing.route', '--read_rr_graph', str(graph), '--route_chan_width', '128', '--num_workers', '1', '--seed', '1', '--check_route', 'full']
        with (physical / 'placement_check.log').open('x') as log:
            code = subprocess.call(command, cwd=physical, env=env, stdout=log, stderr=subprocess.STDOUT)
        text = (physical / 'placement_check.log').read_text()
        assert code == 1 and 'Completed placement consistency check successfully.' in text and 'Cannot open missing.route' in text
        endpoints, after_mapping = extract(physical / 'design.net', physical / 'design.place', graph)
        (physical / 'endpoints.json').write_text(json.dumps(endpoints) + '\n')
        (physical / 'mapping.json').write_text(json.dumps(after_mapping) + '\n')
        assert len(after_mapping['pin_details']) == len(mapping['pin_details'])
        assert all({k: v for k, v in x.items() if k != 'rr_node'} == {k: v for k, v in y.items() if k != 'rr_node'} for x, y in zip(mapping['pin_details'], after_mapping['pin_details']))
        row = dict(name='xtea', exit_code=code, status='GRAPH_AND_ENDPOINTS_CAPTURED', connections=len(endpoints['connections']), files={str(p): sha(p) for p in physical.iterdir() if p.is_file()})
        receipt = directory / 'physical_receipt.json'
        receipt.write_text(json.dumps(dict(bindings={**bindings, str(protocol_path): protocol_digest}, rows=[row])) + '\n')
        demand = directory / 'demand'
        commands = [[str(scripts[0]), str(physical), str(receipt)], [str(scripts[1]), str(physical), str(demand)], [str(scripts[2]), str(demand), str(physical / 'endpoints.json')]]
        terminals = []
        for i, args in enumerate(commands):
            with (directory / ('stage_%d.log' % i)).open('x') as log:
                status = subprocess.call([sys.executable, *args], cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
            terminals.append(dict(command=args, exit_status=status))
            (directory / 'terminals.json').write_text(json.dumps(terminals, indent=2) + '\n')
            if status:
                raise SystemExit(status)
        manifest = directory / 'xtea.queries'
        native_mapping = prepare(demand / 'endpoints.json', manifest)
        after = json.loads((demand / 'endpoints.json').read_text())
        assert len(native_mapping) == len(after['connections']) == len(ep['connections']) == 2450
        assert all((x['connection_id'], x['net_id']) == (y['connection_id'], y['net_id']) for x, y in zip(ep['connections'], after['connections']))
        changed = [y['connection_id'] for x, y in zip(ep['connections'], after['connections']) if (x['source'], x['sink']) != (y['source'], y['sink'])]
        assert changed and sha(protocol_path) == protocol_digest and not list(directory.rglob('*.route'))
        rows.append(dict(**item, endpoint=str(demand / 'endpoints.json'), manifest=str(manifest), changed_connections=changed, preparation_seconds=time.perf_counter() - tick, native_placement_and_endpoint_and_demand_audits_pass=True))
        (out / 'rows.json').write_text(json.dumps(rows, indent=2) + '\n')
        print('CANDIDATE PASS', item['candidate_id'], 'endpoint changes', len(changed), flush=True)
    assert sha(protocol_path) == protocol_digest and all(sha(p) == h for p, h in bindings.items())
    for p in out.rglob('*'):
        if p.is_file():
            bindings[str(p)] = sha(p)
    (out / 'verification.json').write_text(json.dumps(dict(bindings=bindings, rows=rows, all_eight_legal_moves_and_complete_endpoint_identity_pass=True, protocol_frozen_before_preparation=True, native_route_labels_generated=False, sketch_decisions_generated=False, whole_preparation_seconds=time.perf_counter() - begin, scope=protocol['scope']), indent=2) + '\n')
    print('COHORT COMPLETE', len(rows), flush=True)


if __name__ == '__main__':
    main()
