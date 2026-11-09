"""Post-label selected-region NET tracing, exact union counting, no model changes."""
import hashlib
import json
import resource
import struct
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from xml.parsers import expat

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from diagnose_neuron_scaled_hotspot_regions_v1 import nodes_only, keys, stamp
from stream_native_NET_occupancy_v1 import NET, NODE
from observe_neuron_scaled_present_pipeline_v1 import process

OUT = R/'experiments/neuron_proxy_budget_hotspot_NET_owners_v1_2026-10-17'
REGIONS = R/'experiments/neuron_proxy_budget_hotspot_regions_v1_2026-10-17'


def load(path):
    return json.loads(Path(path).read_text())


def main():
    started = time.perf_counter()
    limit = 2*2**30
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    reserve = 0
    assert free >= limit+8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    admission_path = R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17/independent_final_admission_v1.json'
    assert load(admission_path)['all_pass']
    endpoint_path = R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    endpoint = load(endpoint_path)
    region_proof = load(REGIONS/'verification.json')
    assert region_proof['all_pass'] and region_proof['all3_frozen_spatial_metric_sets_exactly_reproduced']
    graph = Path(endpoint['inputs']['graph']['path'])
    native_audit = R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json'
    native_route = R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14/output.route'
    criticality_path = R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json'
    criticality_proof = criticality_path.parent/'verification.json'
    base_proof = R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json'
    base_payload = base_proof.parent/'node_base.u128le'
    frames = {
        'initial': R/'experiments/neuron_continue_primary_trial_v1_2026-10-17/model/initial.json',
        'continued1': R/'experiments/neuron_continue_primary_trial_v1_2026-10-17/model/sketch.json',
        'budget1': R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17/model/sketch.json'}
    bindings = closure([Path(__file__)])
    for path in (admission_path, endpoint_path, REGIONS/'verification.json', native_audit, native_route,
                 criticality_path, criticality_proof, base_proof, base_payload, *frames.values()):
        bindings[str(path)] = sha(path)
        if str(path) in region_proof['bindings']:
            assert bindings[str(path)] == region_proof['bindings'][str(path)]
    assert load(criticality_proof)['bindings'][str(criticality_path)] == bindings[str(criticality_path)]
    assert load(base_proof)['bindings'][str(base_payload)] == bindings[str(base_payload)]
    native = load(native_audit)
    assert native['inputs_sha256']['route'] == bindings[str(native_route)]
    truth = native['node_occupancy']
    del native
    before = {str(p): stamp(p) for p in (graph, native_route, *frames.values())}
    region_bins = {m: row['top20'] for m, row in region_proof['diagnoses'].items()}
    region_bins['native'] = region_proof['native_top20']
    wanted_bins = set().union(*map(set, region_bins.values()))
    selected = {}
    bin_nodes = {key: set() for key in wanted_bins}
    locations = {}
    endpoint_nodes = {q[k] for q in endpoint['connections'] for k in ('source', 'sink')}
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
        graph_expected_sha256=endpoint['graph_sha256'], region_policy='Exactly all initial/continued1/budget1/native top20 bins from the previous complete-region diagnosis, no added threshold or tuned subset.',
        identity='Physical edge IDs are original XML rr_edges order, including CSR reorder preservation. Selected channel occupancy is unique NET union across all connection paths; native NET headers/names must match original endpoint cohort.',
        verification='Every selected resource owner count equals each original ledger; reconstruct ALL native-route node occupancies and match certified physical label exactly; selected bin integer demand matches previous diagnosis.',
        fanout_categories=['1', '2-3', '4-15', '>=16'],
        scope='Post-label exposed-neuron descriptive ownership trace, not changed primary metric, causal mechanism, new model/factor selection, heldout, native candidate QoR or workflow gain.',
        memory_limit_bytes=limit, shared_headroom_bytes=free, remaining_candidate_reservation_bytes=reserve,
        margin_bytes=8*2**30, promoted=False), indent=2)+'\n')
    def collect(node):
        nid = int(node['id'])
        if nid in endpoint_nodes:
            loc = node['loc']
            locations[nid] = [int(loc.get('layer', 0)), *[int(loc[k]) for k in ('xlow', 'ylow', 'xhigh', 'yhigh')]]
        if node['type'] not in ('CHANX', 'CHANY') or int(node['capacity']) == 0:
            return
        touched = wanted_bins.intersection(keys(node))
        if touched:
            selected[nid] = dict(type=node['type'], capacity=int(node['capacity']),
                loc=node['loc'], bins=sorted(touched))
            for key in touched:
                bin_nodes[key].add(nid)
    nodes_only(graph, collect)
    assert endpoint_nodes <= locations.keys() and all(bin_nodes.values())
    # Complete streaming graph scan, no CSR allocation or graph search.
    edge_to_selected, edges, inside = {}, 0, False
    def enter(tag, attrs):
        nonlocal edges, inside
        if tag == 'rr_edges':
            inside = True
        elif tag == 'edge' and inside:
            target = int(attrs['sink_node'])
            if target in selected:
                edge_to_selected[edges] = target
            edges += 1
    def leave(tag):
        nonlocal inside
        if tag == 'rr_edges':
            inside = False
    parser = expat.ParserCreate()
    parser.StartElementHandler, parser.EndElementHandler = enter, leave
    digest = hashlib.sha256()
    with graph.open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            digest.update(block)
            parser.Parse(block, False)
        parser.Parse(b'', True)
    assert edges == 39165143 and digest.hexdigest() == endpoint['graph_sha256']
    bindings[str(graph)] = digest.hexdigest()
    assert set(edge_to_selected.values()) == set(selected)
    comparison_path=R/'experiments/neuron_proxy_budget_full_state_comparison_v1_2026-10-17/verification.json'
    comparison=load(comparison_path);assert comparison['all_pass']
    extra_CIDs=set(comparison['final_paths_using_extra_budget_CIDs']);assert len(extra_CIDs)==1050
    bindings[str(comparison_path)]=sha(comparison_path)
    for path in frames.values():
        if str(path) in comparison['bindings']:assert sha(path)==comparison['bindings'][str(path)]
    extra_owners={nid:set() for nid in selected}
    extra_users={nid:set() for nid in selected}
    owners, histories = {}, {}
    query_by_id = {q['connection_id']: q for q in endpoint['connections']}
    by_net = defaultdict(list)
    for q in endpoint['connections']:
        by_net[q['net_id']].append(q)
    for method, path in frames.items():
        state = load(path)
        assert state['completed_connections'] == state['required_connections'] == 77106
        own = {nid: set() for nid in selected}
        seen = set()
        for record in state['records']:
            cid, net = record['connection_id'], record['net_id']
            assert cid not in seen and all(record[k] == value for k, value in query_by_id[cid].items())
            seen.add(cid)
            for eid in record['answer']['physical_edge_ids']:
                if eid in edge_to_selected:
                    own[edge_to_selected[eid]].add(net)
                    if method=='budget1' and cid in extra_CIDs:
                        extra_owners[edge_to_selected[eid]].add(net)
                        extra_users[edge_to_selected[eid]].add(cid)
        assert seen == set(query_by_id)
        assert all(len(own[nid]) == state['ledger'].get(str(nid), 0) for nid in selected)
        if method=='budget1':assert all(extra_owners[nid]<=own[nid] for nid in selected)
        owners[method] = own
        if method != 'initial':
            # The sketch JSON has no history; use the closed final round frame.
            final_round = path.parent/'round1.json'
            bindings[str(final_round)] = sha(final_round)
            prices = load(final_round)['prices']
            histories[method] = {nid: prices.get(str(nid), 0) for nid in selected}
        del state
    native_owners = {nid: set() for nid in selected}
    native_counts = Counter()
    name_to_net = {name: int(net) for net, name in endpoint['net_names'].items()}
    assert len(name_to_net) == len(endpoint['net_names'])
    route_seen, current, current_name, used = set(), None, None, set()
    def flush():
        if current is None:
            return
        native_counts.update(used)
        if used:
            assert current_name in name_to_net and name_to_net[current_name] == current
            for nid in used.intersection(selected):
                native_owners[nid].add(current)
    with native_route.open() as stream:
        for line in stream:
            match = NET.match(line)
            if match:
                flush()
                current, current_name = int(match[1]), match[2]
                assert current not in route_seen
                route_seen.add(current)
                used = set()
            elif line.lstrip().startswith('Net '):
                raise ValueError('unrecognized NET header')
            elif line.lstrip().startswith('Node:'):
                match = NODE.match(line)
                assert match is not None and current is not None
                used.add(int(match[1]))
    flush()
    assert {str(nid): count for nid, count in native_counts.items()} == truth
    assert all(len(native_owners[nid]) == truth.get(str(nid), 0) for nid in selected)
    owners['native'] = native_owners
    previous_rows = {row['bin']: row for row in region_proof['selected_bin_rows']}
    for key, node_ids in bin_nodes.items():
        capacity = sum(selected[nid]['capacity'] for nid in node_ids)
        assert capacity == previous_rows[key]['capacity']
        for method in owners:
            expected = (previous_rows[key]['native_utilization'] if method == 'native'
                        else previous_rows[key]['predicted_utilizations'][method])
            assert sum(len(owners[method][nid]) for nid in node_ids)/capacity == expected
    criticalities = load(criticality_path)
    assert len(criticalities) == 77106
    by_crit = defaultdict(list)
    for row in criticalities:
        q = query_by_id[row['connection_id']]
        assert (row['net'], row['source_rr'], row['target_rr']) == (q['net_id'], q['source'], q['sink'])
        value = struct.unpack('f', struct.pack('f', float(row['criticality_float32_text'])))[0]
        by_crit[q['net_id']].append(value)
    weight = load(base_proof)['scale']//(20*10**9)
    with base_payload.open('rb') as stream:
        for nid, info in selected.items():
            stream.seek(16*nid)
            info['node_base_integer'] = int.from_bytes(stream.read(16), 'little')
            a = info['loc']
            span = max(int(a['xhigh'])-int(a['xlow']), int(a['yhigh'])-int(a['ylow']))+1
            info['static_floor_integer'] = info['node_base_integer']+weight*span
            info['final_round_price_counter'] = {m: histories[m][nid] for m in histories}
    diagnostics = {}
    for region, bins in region_bins.items():
        node_ids = set().union(*(bin_nodes[key] for key in bins))
        details = {}
        truth_pairs = {(nid, net) for nid in node_ids for net in native_owners[nid]}
        for method, own in owners.items():
            contribution = Counter(net for nid in node_ids for net in own[nid])
            pairs = {(nid, net) for nid in node_ids for net in own[nid]}
            categories = Counter()
            for net, count in contribution.items():
                fanout = len(by_net[net])
                category = '1' if fanout == 1 else '2-3' if fanout <= 3 else '4-15' if fanout < 16 else '>=16'
                categories[category] += count
            top = []
            for net, count in sorted(contribution.items(), key=lambda row: (-row[1], row[0]))[:10]:
                queries = by_net[net]
                top.append(dict(net_id=net, net_name=endpoint['net_names'][str(net)],
                    distinct_selected_channels_owned=count, connection_count=len(queries),
                    minimum_initial_criticality=min(by_crit[net]), maximum_initial_criticality=max(by_crit[net]),
                    source_rr=queries[0]['source'], source_loc=locations[queries[0]['source']]))
            details[method] = dict(physical_channel_NET_pairs=len(pairs), unique_NETs=len(contribution),
                native_same_channel_same_NET_pairs=len(pairs&truth_pairs),
                contribution_by_connection_count=categories, top10_contributing_NETs=top)
        extra_pairs={(nid,net) for nid in node_ids for net in extra_owners[nid]}
        details['budget1']['channel_NET_pairs_touched_by_extra_budget_paths']=len(extra_pairs)
        details['budget1']['native_matching_pairs_touched_by_extra_budget_paths']=len(extra_pairs&truth_pairs)
        details['budget1']['extra_budget_connection_users']=len(set().union(*(extra_users[nid] for nid in node_ids)))
        details['budget1']['NETs_with_extra_budget_paths']=len({net for nid,net in extra_pairs})
        diagnostics[region] = dict(selected_bins=bins, distinct_physical_channels=len(node_ids), methods=details)
    assert all(stamp(path) == value for path, value in before.items())
    assert all(sha(p) == value for p, value in bindings.items() if p != str(graph))
    ownership_path = OUT/'selected_resource_owners.json'
    ownership_path.write_text(json.dumps({m: {str(n): sorted(nets) for n, nets in own.items()} for m, own in owners.items()}, separators=(',', ':'))+'\n')
    (OUT/'selected_resource_metadata.json').write_text(json.dumps(selected, indent=2)+'\n')
    extra_path=OUT/'selected_extra_budget_users.json'
    extra_path.write_text(json.dumps({str(nid):dict(NETs=sorted(extra_owners[nid]),CIDs=sorted(extra_users[nid])) for nid in selected},separators=(',',':'))+'\n')
    for path in [ownership_path,OUT/'selected_resource_metadata.json',extra_path]:bindings[str(path)]=sha(path)
    result = dict(all_pass=True, bindings=bindings, graph_edges_streamed=edges,
        selected_physical_channels=len(selected), selected_incoming_edge_IDs=len(edge_to_selected),
        all_selected_resource_model_owner_counts_equal_ledgers=True,
        full_native_route_unique_NET_occupancy_equals_certified_label=True,
        all_selected_bin_demands_equal_previous_full_domain_diagnosis=True,
        diagnostics=diagnostics, seconds=time.perf_counter()-started,
        peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        post_label_diagnostic=True, causal_mechanism_proven=False, promoted=False,
        scope='Descriptive identity-preserving selected physical resource ownership trace. No repeated connection/trunk counting. Final-round price counters are stored metadata, not actual per-search snapshots or a causal price attribution. Native route legality comes from prior external audits; no new router/model run or metric changes.')
    (OUT/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('bindings', 'diagnostics')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
