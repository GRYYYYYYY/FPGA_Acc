"""Exposed-design error localization; never changes metrics or chooses a model."""
import hashlib
import json
import resource
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from xml.parsers import expat

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
from observe_neuron_scaled_present_pipeline_v1 import process

OUT = R/'experiments/neuron_scaled_hotspot_regions_v1_2026-10-17'
COMPARISON = R/'experiments/neuron_scaled_present_full_comparison_v2_2026-10-17'


def load(path):
    return json.loads(Path(path).read_text())


def stamp(path):
    s = Path(path).stat()
    return s.st_size, s.st_mtime_ns, s.st_ino


def nodes_only(path, callback):
    stack, current = [], [None]
    class Finished(Exception):
        pass
    def start(tag, attrs):
        parent = stack[-1] if stack else None
        if tag == 'node' and parent == 'rr_nodes':
            current[0] = dict(attrs)
        elif parent == 'node' and tag in ('loc', 'segment') and current[0] is not None:
            current[0][tag] = dict(attrs)
        stack.append(tag)
    def end(tag):
        if tag == 'node' and len(stack)>1 and stack[-2] == 'rr_nodes':
            callback(current[0])
            current[0] = None
        assert stack.pop() == tag
        if tag == 'rr_nodes':
            raise Finished()
    parser = expat.ParserCreate()
    parser.StartElementHandler, parser.EndElementHandler = start, end
    with Path(path).open('rb') as stream:
        try:
            parser.ParseFile(stream)
        except Finished:
            pass


def keys(node):
    loc, segment = node['loc'], node['segment']['segment_id']
    for x in range(int(loc['xlow']), int(loc['xhigh'])+1):
        for y in range(int(loc['ylow']), int(loc['yhigh'])+1):
            yield f"{loc.get('layer', '0')},{x},{y},{node['type']},{segment}"


def main():
    started = time.perf_counter()
    live_root = R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17'
    metadata = load(live_root/'model_process.json')
    live = process(metadata['pid'], int(metadata['start_stat'].rsplit(')', 1)[1].split()[19]), metadata['args'])
    assert live['verified_live']
    limit = 2*2**30
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    reserve = max(0, 20*2**30-live['memory_KiB']['VmSize']*1024)
    assert free >= reserve+limit+8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    certified = load(COMPARISON/'verification.json')
    assert certified['all_pass'] and certified['independently_checked_metric_sets'] == 12
    endpoint = R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    graph = Path(load(endpoint)['inputs']['graph']['path'])
    truth_path = R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json'
    assert str(truth_path) in certified['bindings']
    frames = {'initial': R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15/model/initial.json'}
    for factor in (1, 2, 4):
        frames[str(factor)] = R/f'experiments/titan23_neuron_scaled_present_factor{factor}_pipeline_v1_2026-10-15/model/sketch.json'
    bindings = closure([Path(__file__)])
    for p in (COMPARISON/'verification.json', endpoint, truth_path, *frames.values()):
        bindings[str(p)] = sha(p)
        if str(p) in certified['bindings']:
            assert bindings[str(p)] == certified['bindings'][str(p)]
    before = {str(p): stamp(p) for p in (graph, truth_path, *frames.values())}
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
        graph_expected_sha256=load(endpoint)['graph_sha256'],
        policy='Post-label descriptive error localization on already-exposed neuron only. Reproduce all4 frozen spatial primary metric sets; compare lexical top20 overlap, false-positive native utilization and repeated physical channel membership across selected full-span bins. No new candidate or altered k/tie/domain/threshold.',
        memory_limit_bytes=limit, shared_headroom_bytes=free,
        remaining_candidate_reservation_bytes=reserve, margin_bytes=8*2**30,
        heldout=False, promoted=False), indent=2)+'\n')
    truth = load(truth_path)['node_occupancy']
    ledgers = {}
    for method, path in frames.items():
        value = load(path)
        assert value['completed_connections'] == value['required_connections'] == 77106
        ledgers[method] = value['ledger']
        del value
    cap, native = Counter(), Counter()
    predicted = {method: Counter() for method in frames}
    overused = {method: Counter() for method in frames}
    counts = Counter()
    def accumulate(node):
        counts[node['type']] += 1
        c = int(node['capacity'])
        if node['type'] not in ('CHANX', 'CHANY') or c == 0:
            return
        nid = node['id']
        t = truth.get(nid, 0)
        values = {m: ledger.get(nid, 0) for m, ledger in ledgers.items()}
        for key in keys(node):
            cap[key] += c
            native[key] += t
            for m, value in values.items():
                predicted[m][key] += value
                overused[m][key] += value>c
    nodes_only(graph, accumulate)
    assert sum(counts.values()) == 3593250 and counts['CHANX']+counts['CHANY'] == 1678392
    assert len(cap) == 48194
    tv = {key: native[key]/c for key, c in cap.items()}
    pv = {m: {key: values[key]/cap[key] for key in cap} for m, values in predicted.items()}
    native20 = sorted(tv, key=lambda key: (-tv[key], key))[:20]
    selected = {}
    for method in frames:
        expected = certified['metrics']['1' if method == 'initial' else method]['initial' if method == 'initial' else 'sketch']['metrics']['spatial']
        assert compare(pv[method], tv, 20) == expected
        selected[method] = sorted(pv[method], key=lambda key: (-pv[method][key], key))[:20]
    wanted = set(native20).union(*map(set, selected.values()))
    members = {key: [] for key in wanted}
    def membership(node):
        if node['type'] in ('CHANX', 'CHANY') and int(node['capacity'])>0:
            for key in keys(node):
                if key in wanted:
                    members[key].append(node['id'])
    nodes_only(graph, membership)
    rows = []
    for key in sorted(wanted):
        rows.append(dict(bin=key, capacity=cap[key], native_utilization=tv[key],
            predicted_utilizations={m: pv[m][key] for m in frames},
            overused_physical_channels={m: overused[m][key] for m in frames},
            physical_channels=len(members[key])))
    diagnoses = {}
    for method, bins in selected.items():
        occurrences = Counter(nid for key in bins for nid in members[key])
        diagnoses[method] = dict(top20=bins, native20_overlap=len(set(bins)&set(native20)),
            above_or_equal_native_top20_boundary=sum(tv[key]>=tv[native20[-1]] for key in bins),
            native_utilization_min=min(tv[key] for key in bins),
            native_utilization_max=max(tv[key] for key in bins),
            native_utilization_mean=sum(tv[key] for key in bins)/20,
            predicted_over_capacity_bins=sum(pv[method][key]>1 for key in bins),
            unique_physical_channels_across_selected_bins=len(occurrences),
            physical_channel_memberships=sum(occurrences.values()),
            channels_repeated_across_selected_bins=sum(v>1 for v in occurrences.values()),
            maximum_bins_sharing_one_channel=max(occurrences.values()))
    overlaps = {a: {b: len(set(selected[a])&set(selected[b])) for b in frames} for a in frames}
    graph_digest = sha(graph)
    assert graph_digest == load(endpoint)['graph_sha256']
    bindings[str(graph)] = graph_digest
    assert all(stamp(path) == value for path, value in before.items())
    assert all(sha(p) == digest for p, digest in bindings.items() if p != str(graph))
    result = dict(all_pass=True, bindings=bindings,
        all4_frozen_spatial_metric_sets_exactly_reproduced=True,
        complete_spatial_bins=len(cap), complete_original_node_counts=dict(counts),
        native_top20=native20, native20_boundary=tv[native20[-1]],
        selected_top20_overlap_matrix=overlaps, diagnoses=diagnoses,
        selected_bin_rows=rows, seconds=time.perf_counter()-started,
        peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        post_label_diagnostic=True, heldout=False, promoted=False,
        scope='Descriptive full-domain spatial reproduction and selected-region/shared-span diagnosis only. Repeated channel membership is not a new metric or evidence of a metric bug. No causal attribution, changed model/primary metric, unseen-family or full workflow gain.')
    (OUT/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('bindings', 'selected_bin_rows', 'native_top20')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
