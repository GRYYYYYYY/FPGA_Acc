"""All-original-graph construction and all455 static tables; no route searches.

This is isolated cost/representation evidence, never a complete model result.
"""
import json
import resource
import sys
import time
import traceback
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_wide_v1 import load as load_inputs
from compiled_quotient_model_factory_v2 import create, memory, BINARY
from observe_neuron_scaled_present_pipeline_v1 import process

OUT = R/'experiments/neuron_quotient_cache512_construction_v1_2026-10-17'


def main():
    started = time.perf_counter()
    metadata = json.loads((R/'experiments/titan23_neuron_scaled_present_factor4_pipeline_v1_2026-10-15/model_process.json').read_text())
    observed = process(metadata['pid'], int(metadata['start_stat'].rsplit(')', 1)[1].split()[19]), metadata['args'])
    assert observed['verified_live']
    limit = 20*2**30
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    reserve = max(0, 20*2**30-observed['memory_KiB']['VmSize']*1024)
    assert free >= reserve+limit+8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    endpoint = R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    base = R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json'
    criticality = R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality'
    contract = R/'experiments/quotient_cache512_factory_contract_v2_2026-10-17/verification.json'
    shape = R/'experiments/neuron_quotient_cache_shape_v1_2026-10-17'
    proof = json.loads(contract.read_text())
    assert proof['all_pass'] and all(sha(p) == h for p, h in proof['bindings'].items())
    assert json.loads((shape/'independent_verification.json').read_text())['all_pass']
    bindings = closure([Path(__file__)])
    for path in (endpoint, base, criticality/'verification.json', contract,
                 shape/'verification.json', shape/'independent_verification.json', BINARY):
        bindings[str(path)] = sha(path)
    OUT.mkdir()
    (OUT/'process.json').write_text(json.dumps(dict(pid=__import__('os').getpid(),
        start_stat=Path('/proc/self/stat').read_text(), args=[sys.executable, *sys.argv],
        address_space_limit_bytes=limit))+'\n')
    protocol = dict(bindings=bindings, original_connections=77106, original_nodes=3593250,
        original_arcs=39165143, expected_groups=9216, all_endpoint_target_groups=455,
        cache_entries=512, price_floor='original node base + original scale//(20e9)*CHAN span',
        operation='Load original authenticated CSR/electrical inputs, build v2 quotient graph/native workspace, construct native potentials for every fixed endpoint target group in sorted group ID order. No graph.tree/expand, floor search, retained feedback, native router or native label evaluation.',
        cost='Record all loading/authentication/grouping/graph/workspace/table/conversion/report/verification overhead and full process time. No exclusion of setup cost; no complete workflow speedup inference.',
        validation='Check both distance components on every abstract reverse arc for every target, target distances zero, all native raw/floor/reachability encodings exact, and no eviction when all455 unique targets fit.',
        admission=dict(shared_headroom_bytes=free, remaining_factor4_reservation_bytes=reserve,
            limit_bytes=limit, margin_bytes=8*2**30, original_model=observed),
        development_only=True, heldout=False, complete_model=False, promoted=False)
    (OUT/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    def status(phase, **values):
        record = dict(phase=phase, elapsed_seconds=time.perf_counter()-started, memory_KiB=memory(), **values)
        (OUT/'status.json').write_text(json.dumps(record)+'\n')
        print(json.dumps(record), flush=True)
    status('loading_original_inputs')
    graph, digest, nodes, fields, rc, queries = load_endpoints(endpoint)
    node_base, criticalities, input_bindings = load_inputs(endpoint, base, criticality, len(nodes), rc.scale)
    bindings.update(input_bindings)
    assert (len(nodes), len(fields['dest_ranks']), len(queries)) == (3593250, 39165143, 77106)
    load_seconds = time.perf_counter()-started
    status('building_quotient_and_native_workspace')
    candidate = create(fields, rc.increments, [rc.initial(i) for i in range(len(nodes))],
                       nodes, node_base, rc.scale//(20*10**9))
    try:
        lower = candidate.lower
        targets = {}
        for query in queries:
            targets.setdefault(lower.groups[query['sink']], query['sink'])
        assert lower.group_count == 9216 and len(targets) == 455
        status('building_all_fixed_endpoint_tables', abstract_arcs=lower.abstract_arcs)
        consistency = encodings = 0
        checking_seconds = 0.0
        for index, (group, target) in enumerate(sorted(targets.items())):
            native = candidate.table(target)
            tick = time.perf_counter()
            tables = lower.cache[group]
            assert tables[0][group] == tables[1][group] == 0
            for destination, incoming in enumerate(lower.reverse):
                for source, raw, floor in incoming:
                    for distance, increment in zip(tables, (raw, floor)):
                        if distance[destination] is not None:
                            assert distance[source] is not None
                            assert distance[source] <= increment+distance[destination]
                        consistency += 1
            for g, (raw, floor) in enumerate(zip(*tables)):
                assert bool(native.reachable[g]) == (raw is not None)
                for value, buffer in ((raw, native.raw), (floor, native.floor)):
                    decoded = sum(int(buffer[4*g+i]) << (64*i) for i in range(4))
                    assert decoded == (value if value is not None else 0)
                    encodings += 1
            checking_seconds += time.perf_counter()-tick
            if index%16 == 15 or index+1 == len(targets):
                status('building_all_fixed_endpoint_tables', completed_targets=index+1,
                       total_targets=len(targets))
        report = candidate.cache_report()
        assert report['reverse_table_builds'] == report['native_conversions'] == 455
        assert report['lower_cache_evictions'] == 0
        assert report['native_cache_entries'] == report['lower_cache_entries'] == 455
        assert candidate.total_stats[:3] == [0, 0, 0] or tuple(candidate.total_stats[:3]) == (0, 0, 0)
        assert all(sha(p) == h for p, h in bindings.items())
        result = dict(all_pass=True, bindings=bindings, original_graph_sha256=digest,
            all_original_nodes=len(nodes), all_original_arcs=len(fields['dest_ranks']),
            abstract_groups=lower.group_count, abstract_arcs=lower.abstract_arcs,
            all_endpoint_target_tables=455, abstract_arc_component_consistency_checks=consistency,
            native_component_encoding_checks=encodings, graph_search_calls=0,
            load_and_initial_authentication_seconds=load_seconds,
            consistency_and_encoding_seconds=checking_seconds, cache_report=report,
            whole_model_or_quality_or_workflow_gain_proven=False, promoted=False)
        (OUT/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
        status('complete_all455_tables_and_checks')
    finally:
        candidate.close()


if __name__ == '__main__':
    begin = time.perf_counter()
    try:
        main()
    except BaseException:
        if OUT.exists():
            (OUT/'terminal.json').write_text(json.dumps(dict(exit_status=1,
                seconds=time.perf_counter()-begin, error=traceback.format_exc()))+'\n')
        raise
    else:
        (OUT/'terminal.json').write_text(json.dumps(dict(exit_status=0,
            seconds=time.perf_counter()-begin, all455_tables_and_checks_completed=True,
            actual_address_space_limit_bytes=resource.getrlimit(resource.RLIMIT_AS),
            final_memory_KiB=memory(), complete_model=False))+'\n')
