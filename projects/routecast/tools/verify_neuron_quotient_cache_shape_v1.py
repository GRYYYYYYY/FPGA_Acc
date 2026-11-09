"""Independent Expat grouping and list-based two-layer cache replay."""
import hashlib
import json
import random
import resource
import sys
import time
from collections import Counter
from pathlib import Path
from xml.parsers import expat

from compare_complete_receipt_events_stream_v1 import round_items
from study_neuron_quotient_cache_shape_v1 import LRU, OUT, R, sha, stamp


def main():
    resource.setrlimit(resource.RLIMIT_AS, (2**30, 2**30))
    started = time.perf_counter()
    proof = json.loads((OUT/'verification.json').read_text())
    assert proof['all_pass']
    assert all(sha(Path(p)) == h for p, h in proof['bindings'].items())
    endpoint = json.loads(Path(next(p for p in proof['bindings'] if p.endswith('/endpoints.json'))).read_text())
    graph = Path(endpoint['inputs']['graph']['path'])
    original_stamp = stamp(graph)
    needed = {q['sink'] for q in endpoint['connections']}
    counts = Counter()
    found = {}
    current = None
    inside = False
    complete = False
    parser = expat.ParserCreate()

    def enter(name, attr):
        nonlocal current, inside
        if name == 'rr_nodes':
            inside = True
        elif inside and name == 'node':
            current = dict(attr)
        elif inside and current is not None and name == 'loc':
            current['loc'] = dict(attr)
        elif inside and current is not None and name == 'segment':
            current['segment'] = int(attr['segment_id'])

    def leave(name):
        nonlocal current, inside, complete
        if name == 'node' and inside:
            a = current['loc']
            key = (int(a.get('layer', 0)), int(a['xlow'])//4, int(a['ylow'])//4,
                   current['type'], current.get('segment', -1), current.get('direction', 'NONE'))
            counts[key] += 1
            if int(current['id']) in needed:
                assert int(current['id']) not in found
                found[int(current['id'])] = key
            current = None
        elif name == 'rr_nodes':
            inside = False
            complete = True
    parser.StartElementHandler, parser.EndElementHandler = enter, leave
    digest = hashlib.sha256()
    with open(graph, 'rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            digest.update(block)
            if not complete:
                parser.Parse(block, False)
    assert complete and set(found) == needed
    assert digest.hexdigest() == proof['graph_sha256'] and stamp(graph) == original_stamp
    rows = json.loads((OUT/'groups.json').read_text())
    assert Counter({tuple(r['key']): r['physical_nodes'] for r in rows}) == counts
    ids = {tuple(r['key']): r['group_id'] for r in rows}
    assert [ids[k] for k in sorted(ids)] == list(range(len(ids)))
    targets = {q['connection_id']: ids[found[q['sink']]] for q in endpoint['connections']}
    capacities = [r['capacity'] for r in proof['native_cache']]
    states = {k: [[], [], [0, 0, 0], [0, 0, 0]] for k in capacities}

    def touch(cache, stats, target, capacity):
        if target in cache:
            stats[0] += 1
            cache.remove(target)
        else:
            stats[1] += 1
            if len(cache) == capacity:
                cache.pop(0)
                stats[2] += 1
        cache.append(target)

    frequency = Counter()
    trace = hashlib.sha256()
    receipt = Path(next(p for p in proof['bindings'] if p.endswith('/receipt.json')))
    for kind, index, event in round_items(receipt):
        if kind != 'event':
            continue
        for cid in event['primary_search_connection_ids']:
            target = targets[cid]
            frequency[target] += 1
            trace.update(f'{index},{cid},{target}\n'.encode())
            for capacity, (native, lower, ns, ls) in states.items():
                if target not in native:
                    touch(lower, ls, target, capacity)
                touch(native, ns, target, capacity)
    assert trace.hexdigest() == proof['trace_sha256']
    assert sorted(frequency.items()) == [tuple(x) for x in proof['target_frequencies']]
    for column, stats_index in [('native_cache', 2), ('lower_cache', 3)]:
        for row in proof[column]:
            assert states[row['capacity']][stats_index] == [row['hits'], row['builds'], row['evictions']]

    # Exercise the actual frozen production cache classes on a small graph;
    # this tests the inference that native misses need not rebuild lower tables.
    from compiled_quotient_criticality_astar_v1 import Graph
    from static_quotient_lower_bound_v1 import LowerBound
    rng = random.Random(20261017)
    requests = [rng.randrange(5) for _ in range(1000)]
    for capacity in (1, 2, 3, 5):
        lower = LowerBound(dict(row_offsets=[0, 1, 2, 3, 4, 5], dest_ranks=[1, 2, 3, 4, 0]),
                           [1]*5, [0]*5, [1]*5, list(range(5)), max_targets=capacity)
        actual = Graph.__new__(Graph)
        from collections import OrderedDict
        actual.lower, actual.tables = lower, OrderedDict()
        native, abstract = LRU(capacity), LRU(capacity)
        for target in requests:
            if target not in native.cache:
                abstract.touch(target)
            native.touch(target)
            actual.table(target)
            assert list(actual.tables) == list(native.cache)
            assert list(lower.cache) == list(abstract.cache)
        assert (lower.table_builds, lower.cache_hits, lower.evictions) == (abstract.misses, abstract.hits, abstract.evictions)
    result = dict(all_pass=True, producer_result_sha256=sha(OUT/'verification.json'),
        bindings={str(Path(__file__)): sha(Path(__file__)), str(OUT/'groups.json'): sha(OUT/'groups.json')},
        independent_Expat_all_node_group_counts_equal=True,
        full_graph_hash_equal=True, independent_list_cache_full_trace_equal=True,
        frozen_production_cache_requests_checked=4000,
        all_native_and_lower_recencies_equal=True,
        total_seconds=time.perf_counter()-started,
        peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        future_trace_or_workflow_gain_proven=False)
    with open(OUT/'independent_verification.json', 'x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
