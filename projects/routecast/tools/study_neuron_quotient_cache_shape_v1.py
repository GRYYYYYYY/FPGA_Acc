"""Read-only full-node grouping and historical primary-call cache study.

No graph search or native-label access. Historical calls describe the old
trajectory; changed A* ties may change future calls. No cache size is selected.
"""
import hashlib
import json
import resource
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, OrderedDict
from pathlib import Path

from compare_complete_receipt_events_stream_v1 import round_items
from observe_neuron_scaled_present_pipeline_v1 import process

R = Path(__file__).resolve().parents[1]
OUT = R/'experiments/neuron_quotient_cache_shape_v1_2026-10-17'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def stamp(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


class HashingReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        data = self.stream.read(size)
        self.digest.update(data)
        return data


class LRU:
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = self.misses = self.evictions = 0

    def touch(self, key):
        if key in self.cache:
            self.hits += 1
            self.cache.move_to_end(key)
        else:
            self.misses += 1
            self.cache[key] = None
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
                self.evictions += 1

    def result(self):
        return dict(capacity=self.capacity, hits=self.hits, builds=self.misses,
                    evictions=self.evictions,
                    hit_fraction=self.hits/max(1, self.hits+self.misses))


def main():
    start = time.perf_counter()
    memory_limit = 2**30
    model_root = R/'experiments/titan23_neuron_scaled_present_factor4_pipeline_v1_2026-10-15'
    model = json.loads((model_root/'model_process.json').read_text())
    live = process(model['pid'], int(model['start_stat'].rsplit(')', 1)[1].split()[19]), model['args'])
    assert live['verified_live']
    available = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    reserve = max(0, 20*2**30-live['memory_KiB']['VmSize']*1024)
    assert available >= reserve+memory_limit+8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    endpoint = R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    receipt = R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15/model/receipt.json'
    factory = R/'tools/compiled_quotient_model_factory_v1.py'
    bridge = R/'tools/compiled_quotient_criticality_astar_v1.py'
    inputs = json.loads(endpoint.read_text())
    graph = Path(inputs['inputs']['graph']['path'])
    bindings = {str(p): sha(p) for p in (Path(__file__), endpoint, receipt, factory, bridge)}
    before = {str(p): stamp(p) for p in (graph, endpoint, receipt, factory, bridge)}
    sinks = {q['connection_id']: q['sink'] for q in inputs['connections']}
    assert len(sinks) == len(inputs['connections']) == 77106
    needed = set(sinks.values())
    OUT.mkdir()
    protocol = dict(bindings=bindings, original_graph_sha256=inputs['graph_sha256'],
        grouping='layer,xlow//4,ylow//4,type,segment,direction; same as frozen compiled factory v1',
        trace='Every primary_search_connection_ids entry in complete certified factor1 receipt, in stored round/event/list order; includes failed primary attempts, excludes fallback Dijkstra calls and retained pins',
        capacities=[64, 128, 256, 512, 1024], cold_start_once=True,
        cache_semantics='Simulate compiled Graph.table native cache; lower Python cache is consulted only on native miss and can have different recency. Native misses equal potential table conversions, not necessarily reverse-distance rebuilds.',
        memory_model='Payload only: native 2*4*8+8=72 bytes/group/target; Python two tuple pointer arrays add >=16 bytes/group/target on 64-bit. Python integers, tuple/array overallocation, dicts, graph/workspace and transient heaps are extra.',
        admission=dict(limit_bytes=memory_limit, shared_headroom_bytes=available,
                       remaining_model_reservation_bytes=reserve, margin_bytes=8*2**30),
        development_only=True, new_native_labels_used=False,
        limitations='Historical baseline locality is not a future A* trace, timing or quality result. All endpoint groups upper-bound possible targets only for this fixed query set. No policy selected or promoted.')
    (OUT/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    domain = Counter()
    target_keys = {}
    nodes = 0
    # Parse only rr_nodes; hash the entire raw file including all remaining edges.
    with open(graph, 'rb') as stream:
        reader = HashingReader(stream)
        stack = []
        for event, node in ET.iterparse(reader, events=('start', 'end')):
            if event == 'start':
                stack.append(node)
                continue
            if node.tag == 'node' and len(stack) >= 2 and stack[-2].tag == 'rr_nodes':
                loc = node.find('loc').attrib
                segment = node.find('segment')
                key = (int(loc.get('layer', '0')), int(loc['xlow'])//4,
                       int(loc['ylow'])//4, node.get('type'),
                       int(segment.get('segment_id')) if segment is not None else -1,
                       node.get('direction', 'NONE'))
                domain[key] += 1
                nid = int(node.get('id'))
                if nid in needed:
                    assert nid not in target_keys
                    target_keys[nid] = key
                nodes += 1
                stack[-2].remove(node)
            done = node.tag == 'rr_nodes'
            stack.pop()
            if done:
                break
        for _ in iter(lambda: reader.read(2**20), b''):
            pass
        assert reader.digest.hexdigest() == inputs['graph_sha256']
    assert nodes == 3593250 and set(target_keys) == needed
    groups = {key: i for i, key in enumerate(sorted(domain))}
    targets = {cid: groups[target_keys[nid]] for cid, nid in sinks.items()}
    caches = [LRU(k) for k in protocol['capacities']]
    # Model both v1 cache layers: hits in the native cache do not touch lower.cache.
    lower_caches = [LRU(k) for k in protocol['capacities']]
    frequency = Counter()
    rounds = []
    counts = Counter()
    trace_digest = hashlib.sha256()
    for kind, index, item in round_items(receipt):
        if kind == 'metadata':
            rounds.append(dict(round_index=index, **counts,
                               cumulative_native_cache=[c.result() for c in caches],
                               cumulative_lower_cache=[c.result() for c in lower_caches]))
            counts.clear()
            continue
        counts['events'] += 1
        calls = item['primary_search_connection_ids']
        assert len(calls) == item['primary_search_calls'] and len(set(calls)) == len(calls)
        for cid in calls:
            group = targets[cid]
            frequency[group] += 1
            counts['primary_calls'] += 1
            trace_digest.update(f'{index},{cid},{group}\n'.encode())
            for cache, lower in zip(caches, lower_caches):
                if group not in cache.cache:
                    lower.touch(group)
                cache.touch(group)
    assert len(rounds) == 2 and sum(r['events'] for r in rounds) == 101534
    assert all(stamp(Path(p)) == s for p, s in before.items())
    assert all(sha(Path(p)) == h for p, h in bindings.items())
    group_rows = [dict(group_id=groups[k], key=k, physical_nodes=v) for k, v in sorted(domain.items())]
    (OUT/'groups.json').write_text(json.dumps(group_rows, separators=(',', ':'))+'\n')
    n = len(groups)
    result = dict(all_pass=True, bindings=bindings, graph_sha256=inputs['graph_sha256'],
        all_original_nodes=nodes, groups=n, original_connections=len(sinks),
        distinct_sink_nodes=len(needed), all_endpoint_target_groups=len(set(targets.values())),
        observed_primary_target_groups=len(frequency), trace_sha256=trace_digest.hexdigest(),
        rounds=rounds, native_cache=[c.result() for c in caches],
        lower_cache=[c.result() for c in lower_caches],
        target_frequencies=sorted(frequency.items()),
        payload_lower_bounds=[dict(capacity=k, native_bytes=72*n*k,
            native_plus_Python_pointer_bytes=88*n*k) for k in protocol['capacities']],
        full_fixed_endpoint_target_payload_lower_bound=dict(native_bytes=72*n*len(set(targets.values())),
            native_plus_Python_pointer_bytes=88*n*len(set(targets.values()))),
        total_seconds=time.perf_counter()-start, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        future_Astar_locality_proven=False, full_workflow_benefit_proven=False, promoted=False)
    (OUT/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('bindings', 'target_frequencies', 'rounds')}, indent=2), flush=True)


if __name__ == '__main__':
    main()
