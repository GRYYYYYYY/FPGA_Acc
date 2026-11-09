"""All original XTEA connections at one fixed label-free price snapshot.

This is a primitive work experiment, not a whole-model or native QoR result.
"""
import json
import resource
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_wide_v1 import load as load_inputs
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from static_quotient_lower_bound_v1 import LowerBound, Snapshot, Graph
from observe_neuron_scaled_present_pipeline_v1 import process


def main():
    begin = time.perf_counter()
    limit = 2**30
    live = R/'experiments/titan23_neuron_scaled_present_factor4_pipeline_v1_2026-10-15/model_process.json'
    metadata = json.loads(live.read_text())
    model = process(metadata['pid'], int(metadata['start_stat'].rsplit(')', 1)[1].split()[19]), metadata['args'])
    assert model['verified_live']
    reserve = max(0, 20*2**30-model['memory_KiB']['VmSize']*1024)
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= reserve+limit+8*2**30
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    endpoint = R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
    base = R/'experiments/xtea_node_base_wide_v1_2026-10-13/verification.json'
    criticality = R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
    initial_path = R/'experiments/xtea_scaled_present_factor1_pipeline_v1_2026-10-15/model/initial.json'
    contract = R/'experiments/static_quotient_lower_bound_contract_v1_2026-10-17/verification.json'
    proof = json.loads(contract.read_text())
    assert proof['all_pass']
    assert all(sha(p)==h for p,h in proof['bindings'].items())
    bindings = closure([Path(__file__)])
    for path in (endpoint, base, criticality/'verification.json', initial_path, contract):
        bindings[str(path)] = sha(path)
    out = R/'experiments/xtea_static_quotient_lower_bound_v1_2026-10-17'
    out.mkdir()
    (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
        all_connections=2450, spatial_pitch=4, target_group_LRU_entries=64,
        grouping='layer,xlow//4,ylow//4,type,segment,direction; dense IDs from sorted keys',
        price='frozen structural node base + original static span weight; all history/present factors are nonnegative additions, so this is a floor, not actual transaction snapshots',
        query_policy='Original connection-ID order, fresh source-only tree for every query, initialized criticality and original raw budget. Zero-heuristic and quotient A* alternate order by connection index. Independent arbitrary-integer reference on every query.',
        tie_policy='A* heap(f,g,node), original CSR strict relax. Equal weighted paths may differ in raw cost, budget status and later trajectories; no old path/state parity promised.',
        cost_policy='Record setup/table construction/all searches and complete arc consistency audit. Work counts are not compiled/runtime/full-workflow acceleration.',
        development_only=True, new_native_route_labels_used=False,
        resource_admission=dict(shared_headroom_bytes=free, child_limit_bytes=limit,
                                remaining_factor4_reservation_bytes=reserve, margin_bytes=8*2**30),
        scope='Full original XTEA connection primitive at a single static floor snapshot. No retained/shared NET schedule, owner-excluded feedback, whole-model quality, factor selection, native QoR, heldout or hardware result.'),indent=2)+'\n')
    load_tick = time.perf_counter()
    graph, digest, nodes, fields, rc, queries = load_endpoints(endpoint)
    node_base, criticalities, input_bindings = load_inputs(endpoint, base, criticality, len(nodes), rc.scale)
    for p,h in input_bindings.items():
        assert p not in bindings or bindings[p]==h
        bindings[p]=h
    bindings[str(graph)] = digest
    assert len(queries)==2450
    initial_state=json.loads(initial_path.read_text())
    budgets={r['connection_id']:r['budget_integer'] for r in initial_state['records']}
    assert len(budgets)==2450
    weight=rc.scale//(20*10**9)
    floors=[]
    keys=[]
    for n,node in enumerate(nodes):
        loc=node.find('loc').attrib
        span=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.get('type') in ('CHANX','CHANY') else 0
        floors.append(node_base[n]+weight*span)
        segment=node.find('segment')
        keys.append((int(loc.get('layer','0')),int(loc['xlow'])//4,int(loc['ylow'])//4,
                     node.get('type'),int(segment.get('segment_id')) if segment is not None else -1,node.get('direction','NONE')))
    domain={key:i for i,key in enumerate(sorted(set(keys)))}
    groups=[domain[key] for key in keys]
    raw=tuple(rc.increments)
    initial=tuple(rc.initial(i) for i in range(len(nodes)))
    load_seconds=time.perf_counter()-load_tick
    setup=time.perf_counter()
    lower=LowerBound(fields,raw,initial,floors,groups,max_targets=64)
    zero=LowerBound(fields,raw,initial,floors,[0]*len(nodes),max_targets=1)
    candidate,baseline,oracle=Graph(lower),Graph(zero),Reference(fields,raw,initial)
    snapshots=[Snapshot(zero,floors),Snapshot(lower,floors)]
    setup_seconds=time.perf_counter()-setup
    assert all(sha(p)==h for p,h in bindings.items())
    rows=[];seconds=[0.,0.];statuses=[Counter(),Counter()];budget_status_differences=0;path_differences=0
    for index,query in enumerate(sorted(queries,key=lambda q:q['connection_id'])):
        c=criticalities[query['connection_id']]
        assert (c['net'],c['source_rr'],c['target_rr'])==(query['net_id'],query['source'],query['sink'])
        fraction=Fraction(c['criticality_numerator'],c['criticality_denominator'])
        budget=budgets[query['connection_id']];results={}
        for method in ((0,1) if index%2==0 else (1,0)):
            tree=(baseline if method==0 else candidate).tree(query['source'])
            tick=time.perf_counter()
            result=tree.expand(query['sink'],fraction,snapshots[method],budget)
            seconds[method]+=time.perf_counter()-tick;results[method]=result;statuses[method][result['status']]+=1
            if not result['committed']:
                assert tree.parents=={} and tree.arrival=={query['source']:initial[query['source']]}
        expected=oracle.tree(query['source']).expand(query['sink'],fraction,snapshots[0],budget)
        assert results[0]==expected
        assert results[1]['objective_numerator']==expected['objective_numerator']
        assert results[1]['objective_denominator']==expected['objective_denominator']
        for result in results.values():
            u=query['source'];paid=initial[u];cost=fraction.numerator*paid;seen={u}
            for slot in result['path_slots']:
                assert fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1]
                u=fields['dest_ranks'][slot];assert u not in seen;seen.add(u);paid+=raw[slot]
                cost+=fraction.numerator*raw[slot]+(fraction.denominator-fraction.numerator)*floors[u]
            assert u==query['sink'] and paid==result['raw'] and cost==result['objective_numerator']
            assert result['committed']==(paid<=budget)
        budget_status_differences+=results[0]['status']!=results[1]['status']
        path_differences+=results[0]['path_slots']!=results[1]['path_slots']
        rows.append(dict(connection_id=query['connection_id'],objective_numerator=str(expected['objective_numerator']),
                         objective_denominator=fraction.denominator,baseline_raw=str(results[0]['raw']),
                         candidate_raw=str(results[1]['raw']),baseline_status=results[0]['status'],candidate_status=results[1]['status']))
    # Fresh lower-bound instance: audit both potentials on every original arc for
    # every actually requested target group, independently of A* visited nodes.
    audit_tick=time.perf_counter();audit=LowerBound(fields,raw,initial,floors,groups,max_targets=1)
    targets={groups[q['sink']]:q['sink'] for q in queries};checks=0
    for target in targets.values():
        tables=audit.tables(target)
        for u in range(len(nodes)):
            for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
                v=fields['dest_ranks'][slot]
                for table,increment in ((tables[0],raw[slot]),(tables[1],floors[v])):
                    a,b=table[groups[u]],table[groups[v]]
                    if b is not None:assert a is not None and a<=increment+b
                    checks+=1
    audit_seconds=time.perf_counter()-audit_tick
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'queries.json').write_text(json.dumps(rows,indent=2)+'\n')
    result=dict(bindings=bindings,all_pass=True,all_original_connections=2450,
        nodes=len(nodes),arcs=len(raw),groups=lower.group_count,abstract_arcs=lower.abstract_arcs,
        requested_target_groups=len(targets),original_arc_component_consistency_checks=checks,
        all_weighted_objectives_equal_reference=True,all_original_paths_and_raw_costs_reconstructed=True,
        baseline_zero_heuristic_exact_result_path_and_budget_parity_with_reference=True,
        baseline_work=dict(settled=baseline.settled,scanned=baseline.scanned,pushes=baseline.pushes),
        candidate_work=dict(settled=candidate.settled,scanned=candidate.scanned,pushes=candidate.pushes),
        candidate_table_builds=lower.table_builds,cache_hits=lower.cache_hits,evictions=lower.evictions,
        baseline_status_counts=dict(statuses[0]),candidate_status_counts=dict(statuses[1]),
        budget_status_differences=budget_status_differences,path_differences=path_differences,
        load_seconds=load_seconds,setup_seconds=setup_seconds,
        interleaved_query_seconds=dict(baseline=seconds[0],candidate=seconds[1]),
        full_arc_consistency_audit_seconds=audit_seconds,total_process_seconds=time.perf_counter()-begin,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        compiled_or_full_workflow_gain_proven=False,complete_feedback_model_executed=False,
        scope='All2450 original XTEA queries at one static price-floor snapshot; exact weighted objectives and full directed original-arc lower-bound consistency. Source-only independent searches and arbitrary-integer Python implementation; setup/cache/validation costs retained. Changed ties may affect raw paths/budgets. No complete retained NET feedback, prediction quality, native QoR, unseen families, hardware or full workflow result.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','scope')},indent=2),flush=True)


if __name__=='__main__':
    main()
