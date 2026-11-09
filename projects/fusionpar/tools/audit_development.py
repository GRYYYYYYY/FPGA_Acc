#!/usr/bin/env python3
"""Independently reconstruct archived FP publications and timing barriers.

Checks full serialized state, per-object version changes, native certificates,
strict research QoR gates, snapshot consumption and archived SHA-256 bindings.
Protocol-only successful commits are counted separately from research results.
"""
import argparse
import csv
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import struct

from prepare_vpr_bundle import sha
from validate_candidate import read_state, physical_digest


def require(condition, message):
    if not condition:
        raise ValueError(message)


def semantic_digest(state):
    placement, routes, resources, epochs, criticalities, site_versions = state
    value = 14695981039346656037
    def word(number):
        nonlocal value
        for byte in struct.pack('<Q', number):
            value = ((value ^ byte) * 1099511628211) & ((1 << 64)-1)
    for number in epochs:
        word(number)
    word(len(placement))
    for row in placement:
        for number in row:
            word(number)
    word(len(site_versions))
    for number in site_versions:
        word(number)
    word(len(routes))
    for route in routes:
        for number in (route['source'], route['sink'], route['version'], len(route['path']), *route['path']):
            word(number)
    word(len(resources))
    for row in resources:
        for number in row:
            word(number)
    word(len(criticalities))
    for number in criticalities:
        word(number)
    return f'{value:016x}'


def publication(before, after, event, connections, routing_epoch=False):
    old_place, old_routes, old_resources, old_epochs, old_timing, old_sites = before
    new_place, new_routes, new_resources, new_epochs, new_timing, new_sites = after
    require(new_epochs == (old_epochs[0]+1, *old_epochs[1:]), 'publication changed wrong epochs')
    require(old_timing == new_timing, 'move publication changed timing snapshot')
    moved = {i for i, (a, b) in enumerate(zip(old_place, new_place)) if a[0] != b[0]}
    if routing_epoch:
        require(not moved and not event['moves'] and event['phase']=='routing_epoch', 'fixed-placement epoch changed placement')
        require(event['affected_nets']==len({c['net'] for c in connections}) and event['affected_connections']==len(connections), 'routing epoch did not cover all nets')
    else:
        require(bool(moved), 'claimed move commit changed no position')
    sites = {s for i in moved for s in (old_place[i][0], new_place[i][0])}
    require(len(old_place) == len(new_place) and len(old_sites) == len(new_sites), 'placement dimensions changed')
    for i, (a, b) in enumerate(zip(old_place, new_place)):
        require(b[1] == a[1] + (i in moved), 'placement version not incremented exactly once')
    for i, (a, b) in enumerate(zip(old_sites, new_sites)):
        require(b == a + (i in sites), 'site version not incremented exactly once')
    all_nets = {c['net'] for c in connections}
    affected = {c['net'] for c in connections if c['source_instance'] in moved or c['sink_instance'] in moved}
    if event['affected_nets'] == len(all_nets) and event['affected_connections'] == len(connections):
        affected = all_nets
    expected_connections = {i for i, c in enumerate(connections) if c['net'] in affected}
    retained = set(event.get('retained_connections', []))
    require(retained <= expected_connections, 'retention outside affected scope')
    require(event['affected_nets'] == len(affected) and event['affected_connections'] == len(expected_connections), 'affected scope mismatch')
    touched = set()
    require(len(old_routes) == len(new_routes) == len(connections), 'route dimensions changed')
    for i, (a, b) in enumerate(zip(old_routes, new_routes)):
        if i in expected_connections:
            if i in retained:
                require(a == b, 'retained route/endpoint/version changed')
            else:
                require(b['version'] == a['version']+1, 'route version not incremented once')
            touched.update(a['path'])
            touched.update(b['path'])
        else:
            require(a == b, 'unaffected route changed')
    require(event['touched_resources'] == len(touched), 'resource footprint mismatch')
    require(len(old_resources) == len(new_resources), 'resource dimensions changed')
    for i, (a, b) in enumerate(zip(old_resources, new_resources)):
        require(b[3] == a[3]+(i in touched), 'resource version not incremented exactly once')
        require((a[1], *a[4:]) == (b[1], *b[4:]), 'private PR costs leaked into authoritative state')
        if i not in touched:
            require(a == b, 'untouched resource changed')


def audit(root):
    receipt = json.loads((root/'audit.json').read_text())
    for relative, digest in receipt['artifacts'].items():
        require(sha(root/relative) == digest, 'changed archive: '+relative)
    for entry in receipt['sources']:
        require(sha(entry['snapshot']) == entry['sha256'], 'changed frozen implementation')
    require(sha(root/'build/fusionpar_host') == receipt['host_sha256'], 'host binary changed')
    manifest = json.loads((root/'bundle/manifest.json').read_text())
    rr_backend = manifest.get('rr_export', {'backend':'xml'})['backend']
    if 'rr_export_backend' in receipt:
        require(rr_backend == receipt['rr_export_backend'] and rr_backend in ('xml','sqlite'),
                'RR export backend differs from bundle')
    counters = {'runs': 0, 'qor_commits': 0, 'protocol_commits': 0, 'aborts': 0, 'timing_barriers': 0,
                'placement_repairs': 0, 'native_feedback_checks': 0, 'baseline_route_commits': 0}
    for record in receipt['records']:
        run = Path(record['directory'])
        if 'route_tree_timing_weight_q' in receipt:
            weight = receipt['route_tree_timing_weight_q']
            require(0 <= weight <= 256 and record['summary']['route_tree_timing_weight_q'] == weight,
                    'router timing configuration differs from suite')
            command = record['process']['command']
            require(len(command) == 7 and command[-1] == str(weight), 'host command timing weight mismatch')
        if receipt.get('validation_cost_profile'):
            expected_phases = ['manifest_read', 'bindings_before', 'candidate_read',
                'placement_export_and_contract_check', 'route_decode_and_accounting',
                'rr_metadata_lookup' if rr_backend == 'sqlite' else 'rr_graph_decode',
                'route_export', 'native_check', 'timing_export', 'bindings_after',
                'certificate_and_bridge_write', 'tail_or_failure']
            total_ns = 0
            for directory in run.glob('validation_*'):
                costs = json.loads((directory/'costs.json').read_text())
                phases = costs['phases']
                require(costs['schema'] == receipt['validation_cost_profile'] and
                        all(isinstance(p['wall_ns'], int) and p['wall_ns'] >= 0 for p in phases) and
                        sum(p['wall_ns'] for p in phases) == costs['total_ns'], 'invalid validation cost accounting')
                if costs['complete']:
                    require([p['phase'] for p in phases] == expected_phases and
                            (directory/'validation.json').exists(), 'complete cost profile lacks expected phases/certificate')
                else:
                    require(not (directory/'validation.json').exists(), 'incomplete profile has a success certificate')
                total_ns += costs['total_ns']
            require(total_ns <= record['summary']['native_ns'], 'profiled validation time exceeds containing host interval')
        states, certificates, native_delays = {}, {}, {}
        for path in run.glob('validation_*/validation.json'):
            cert = json.loads(path.read_text())
            if 'rr_export_backend' in receipt:
                require(cert['rr_export_backend'] == rr_backend, 'native certificate used wrong RR backend')
            state_path = path.parent/'candidate.state'
            state = read_state(state_path)
            digest = semantic_digest(state)
            require(cert['legal'] and cert['candidate_sha256'] == sha(state_path), 'native candidate binding mismatch')
            require(cert['physical_state_sha256'] == physical_digest(state), 'native physical binding mismatch')
            require(cert['native_report_sha256'] == sha(path.parent/'native.json'), 'native report changed')
            if digest in states:
                require(states[digest] == state, 'semantic digest collision')
            states[digest] = state
            certificates[digest] = cert
            if (cert.get('timing') or {}).get('delays_sha256'):
                delay_path = path.parent/'connection_delays.txt'
                require(sha(delay_path) == cert['timing']['delays_sha256'], 'native delays changed')
                values = list(map(int, delay_path.read_text().split()))
                require(values[0] == len(values)-1 == len(manifest['connections']), 'native delay coverage mismatch')
                require(sha(path.parent/'timing.output.csv') == cert['timing']['output_sha256'], 'native timing CSV changed')
                with (path.parent/'timing.output.csv').open(newline='') as stream:
                    rows = list(csv.DictReader(stream))
                by_id = {int(row['task_id']): int(row['delay_ps']) for row in rows}
                require(len(rows) == len(by_id) == values[0] and
                        values[1:] == [by_id[i] for i in range(values[0])], 'delay bridge differs from native STA')
                native_delays[digest] = values[1:]
        timing_events = record['timing_events']
        for event in timing_events:
            before = states[event['before']]
            path = run/f"validation_{event['validation_index']}"
            require(semantic_digest(read_state(path/'candidate.state')) == event['before'], 'timing source state mismatch')
            certificate = json.loads((path/'validation.json').read_text())
            require(certificate['timing'] is not None, 'timing barrier lacks STA output')
            require(sha(path/'timing.txt') == certificate['timing']['criticalities_sha256'], 'timing snapshot changed')
            values = list(map(int, (path/'timing.txt').read_text().split()))
            require(values[0] == len(values)-1 == len(before[4]) == event['connections'], 'timing coverage mismatch')
            after = list(deepcopy(before))
            after[3] = (before[3][0]+1, before[3][1]+1, before[3][0])
            after[4] = values[1:]
            after = tuple(after)
            require(event['basis_revision'] == before[3][0] and event['timing_epoch'] == after[3][1], 'timing version mismatch')
            require(semantic_digest(after) == event['after'], 'timing snapshot was not applied exactly')
            states[event['after']] = after
            certificates[event['after']] = certificate
            if event['before'] in native_delays:
                native_delays[event['after']] = native_delays[event['before']]
            counters['timing_barriers'] += 1
        initial = read_state(run/'validation_0/candidate.state')
        baseline = certificates[semantic_digest(initial)]
        current = semantic_digest(initial)
        timing_cursor = 0
        def barriers():
            nonlocal current, timing_cursor
            while timing_cursor < len(timing_events) and timing_events[timing_cursor]['before'] == current:
                current = timing_events[timing_cursor]['after']
                timing_cursor += 1
        barriers()
        events = [json.loads(line) for line in (run/'events.jsonl').read_text().splitlines()]
        budgeted = record['mode'] in ('interleaved_tree_reuse', 'interleaved_tree_feedback') and 'evaluation_budget' in record['summary']
        if record['mode'] == 'interleaved_tree_feedback':
            require(budgeted, 'feedback mode lacks total evaluation budget')
        if budgeted:
            require(record['summary']['evaluation_budget'] == receipt['attempts'] and
                    record['summary']['evaluations'] == len(events) <= receipt['attempts'],
                    'feedback/control exceeded or misreported evaluation budget')
        parent, repair_count, layouts = None, 0, set()
        for evaluation_index, event in enumerate(events):
            require(event['before'] == current, 'event history is disconnected')
            if budgeted:
                require(event['phase'] in ('primary', 'placement_repair'), 'unexpected budgeted phase')
                if event['phase'] == 'primary':
                    require(event['proposal'] == evaluation_index, 'primary ID does not count repair evaluations')
                elif record['mode'] != 'interleaved_tree_feedback':
                    require(False, 'blind control used placement repair')
            if 'moves' in event:
                moves = event['moves']
                require(len({m[0] for m in moves}) == len(moves), 'duplicate moved instance')
                layout = [p[0] for p in states[current][0]]
                for instance, old, new, version in moves:
                    require(states[current][0][instance] == (old, version), 'move uses stale placement')
                    layout[instance] = new
                if record['mode'] == 'interleaved_placement_repair' or budgeted:
                    require(tuple(layout) not in layouts, 'controller repeated a placement')
                    layouts.add(tuple(layout))
                if event['phase'] == 'primary':
                    parent, repair_count = event, 0
                    if event['feedback_kind'] == 'native_delay':
                        candidate = event['candidate_digest']
                        require(candidate in native_delays and current in native_delays, 'native feedback lacks source snapshots')
                        old, new = native_delays[current], native_delays[candidate]
                        expected = [i for i in range(len(old)) if new[i] > old[i]]
                        expected.sort(key=lambda i: (-states[current][4][i], -(new[i]-old[i]), i))
                        require(event['feedback_connections'] == expected and not event['feedback_resources'], 'native feedback witnesses/order mismatch')
                        counters['native_feedback_checks'] += 1
                elif event['phase'] == 'placement_repair':
                    repair_count += 1
                    require(parent is not None and parent['status'] in ('route_failed', 'quality_rejected') and
                            event['proposal'] == parent['proposal'] and event['before'] == parent['before'], 'repair lacks failed parent')
                    require(event['repair_index'] == repair_count <= 2, 'repair budget/order mismatch')
                    for key in ('feedback_kind', 'feedback_connections', 'feedback_resources'):
                        require(event[key] == parent[key], 'repair changed trigger evidence')
                    primary = None
                    for witness in parent['feedback_connections']:
                        net = manifest['connections'][witness]['net']
                        members = {c[k] for c in manifest['connections'] if c['net'] == net
                                   for k in ('source_instance', 'sink_instance')}
                        primary = next((m for m in parent['moves'] if m[0] in members), None)
                        if primary is not None:
                            break
                    require(primary is not None, 'repair has no implicated moved instance')
                    replacement = next((m for m in moves if m[0] == primary[0]), None)
                    require(replacement is not None, 'repair did not move implicated instance')
                    def distance(move):
                        a, b = (manifest['sites'][move[i]] for i in (1, 2))
                        return sum(abs(a[k]-b[k]) for k in ('x', 'y', 'subtile'))
                    require(distance(replacement) <= distance(primary), 'repair exceeds failed move radius')
                    require(sorted((m[0], m[2]) for m in moves) != sorted((m[0], m[2]) for m in parent['moves']), 'repair repeats failed move')
                    counters['placement_repairs'] += 1
                if event['status'] in ('quality_rejected', 'committed'):
                    require(event['candidate_digest'] in certificates, 'candidate missing native certificate')
                    require([p[0] for p in states[event['candidate_digest']][0]] == layout, 'native candidate differs from proposed placement')
                    if record['mode'] in ('interleaved_tree_reuse', 'interleaved_tree_feedback', 'sequential_tree_reuse', 'sequential_shared_tree_reuse'):
                        before, after = states[current], states[event['candidate_digest']]
                        moved = {m[0] for m in moves}
                        affected = {c['net'] for c in manifest['connections'] if c['source_instance'] in moved or c['sink_instance'] in moved}
                        expected = [i for i,c in enumerate(manifest['connections']) if c['net'] in affected and
                                    (before[1][i]['source'],before[1][i]['sink']) == (after[1][i]['source'],after[1][i]['sink'])]
                        require(event['retained_connections'] == expected, 'retention set differs from unchanged endpoints')
                    else:
                        require(not event.get('retained_connections'), 'retention used outside reuse mode')
                    if event['status'] == 'quality_rejected':
                        publication(states[current], states[event['candidate_digest']], event, manifest['connections'])
            if event['status'] == 'committed':
                require(event['after'] in certificates, 'commit lacks independent native validation')
                publication(states[current], states[event['after']], event, manifest['connections'],record['mode']=='route_only')
                if record['mode'] == 'route_only':
                    require(record['summary']['acceptance']=='native_legality_only_FIXED_PLACEMENT_PR_BASELINE', 'routing baseline mislabeled')
                    counters['baseline_route_commits'] += 1
                elif record['mode'] == 'protocol_probe':
                    require(record['summary']['acceptance'] == 'native_legality_only_PROTOCOL_TEST', 'protocol result mislabeled')
                    counters['protocol_commits'] += 1
                else:
                    candidate, previous = certificates[event['after']], certificates[current]
                    require(Decimal(str(candidate['cpd_ns'])) <= Decimal(str(baseline['cpd_ns']))*Decimal('1.02'), 'research commit violates CPD gate')
                    require(candidate['wirelength']*100 <= baseline['wirelength']*102, 'research commit violates WL gate')
                    require((candidate['wirelength'], Decimal(str(candidate['cpd_ns']))) <
                            (previous['wirelength'], Decimal(str(previous['cpd_ns']))), 'research commit violates progress objective')
                    counters['qor_commits'] += 1
                current = event['after']
            else:
                require(event['after'] == current, 'abort changed authoritative state')
                counters['aborts'] += 1
            barriers()
        require(timing_cursor == len(timing_events), 'unconsumed/disconnected timing barrier')
        require(record['summary']['commits'] == sum(e['status']=='committed' for e in events) and
                record['summary']['aborts'] == sum(e['status']!='committed' for e in events), 'summary event totals differ')
        require(record['summary']['placement_repairs'] == sum(e['phase']=='placement_repair' for e in events),
                'summary placement repair count differs')
        require(read_state(run/'final.state') == states[current], 'final full state differs from reconstructed publication history')
        require(sha(run/'final.state') == record['final_state_sha256'], 'final SHA changed')
        counters['runs'] += 1
    return {'schema': 'FUSIONPAR_INDEPENDENT_PUBLICATION_AUDIT_V1', 'pass': True,
            'suite': str(root), 'suite_audit_sha256': sha(root/'audit.json'),
            'auditor_sha256': sha(Path(__file__)), 'counts': counters,
            'scope': 'full serialized state/version/timing reconstruction and archived native bindings; not independent P&R performance replication'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('suite', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.suite.resolve())
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
