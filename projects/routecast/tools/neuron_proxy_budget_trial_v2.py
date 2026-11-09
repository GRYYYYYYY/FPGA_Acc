"""Prepared continue-after-rejection causal trial; explicit stages after baseline closure.

No retry/adoption of started stages. All scientific parameters stay frozen.
"""
import argparse
import datetime
import gc
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from collections import defaultdict
from audit_continue_primary_event_v1 import POLICY as COMPLETION_POLICY

from run_neuron_quotient_astar_pipeline_v1 import (
    R, ENDPOINT, BASE, CRITICALITY,
    load, write, check, gone, EVENT_FLAGS, PHYSICAL)
from audit_proxy_budget_initial_parity_v1 import audit as audit_initial_parity, protocol as audit_protocol
BASELINE=R/'experiments/neuron_continue_primary_trial_v1_2026-10-17'
BASELINE_METRICS=BASELINE/'metrics'
PHYSICAL_TOOL=R/'tools/verify_proxy_budget_demand_frame_v1.py'
from compiled_quotient_model_factory_v2 import BINARY
from compare_complete_receipt_events_stream_v1 import round_items
from neuron_scaled_present_frame_metrics_v1 import evaluate_frame

sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure

OUT = R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17'
PREREG = R/'experiments/neuron_criticality_proxy_budget_prereg_v1_2026-10-17'
BASELINE_QUEUE = R/'experiments/neuron_continue_primary_full_chain_v1_2026-10-17'
DRIVER = R/'tools/run_design_scoped_quotient_astar_proxy_budget_v1.py'
EVENT_TOOL = R/'tools/verify_proxy_budget_full_schedule_v1.py'
REFERENCE = R/'experiments/neuron_certified_native_metrics_v1_2026-10-15'
POLICY = 'fanout>=16; keep old paths with no globally overused node before virtual owner release; no forced timing flags; wholeNET fallback may revise retained paths'


def baseline_gate():
    path = BASELINE_QUEUE/'terminal.json'
    assert path.exists(), 'Current complete baseline chain has not finished'
    terminal = load(path)
    assert terminal['exit_status'] == 0 and terminal['full_model_all3audits_closed_admission_and_all8_metrics_completed'] is True
    assert gone(BASELINE_QUEUE), 'Baseline chain owner still live/unknown'
    admission = load(BASELINE/'independent_final_admission_v1.json')
    assert admission['all_pass'] and admission['all_original_connections'] == 77106 and admission['all_events'] == 101534
    metrics = load(BASELINE_METRICS/'verification.json')
    assert metrics['all_pass'] and metrics['independently_checked_metric_sets'] == 8
    assert metrics['promoted'] is False
    check(admission['bindings'])
    check(metrics['bindings'])
    return {str(p): sha(p) for p in (path, BASELINE/'independent_final_admission_v1.json',
                                   BASELINE_METRICS/'verification.json')}


def prepare():
    receipts=[PREREG/'verification.json',R/'experiments/proxy_budget_integration_ast_contract_v1_2026-10-17/verification.json',R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/closed_admission_v1.json',R/'experiments/proxy_budget_full_auditor_negative_v1_2026-10-17/verification.json']
    for path in receipts:
        proof=load(path);assert proof['all_pass'];check(proof['bindings'])
    bindings = closure([Path(__file__), DRIVER, EVENT_TOOL, PHYSICAL_TOOL])
    for p in (PREREG/'protocol.json', PREREG/'verification.json',
        BASELINE/'protocol.json', BASELINE_METRICS/'verification.json', ENDPOINT, BASE,
        CRITICALITY/'verification.json', BINARY, REFERENCE/'label_admission.json',
        R/'experiments/continue_primary_interface_contract_v1_2026-10-17/verification.json'):
        bindings[str(p)] = sha(p)
    for path in receipts:bindings[str(path)]=sha(path)
    check(bindings)
    OUT.mkdir()
    write(OUT/'protocol.json', dict(bindings=bindings,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        original_connections=77106, nets_per_round=50767, rounds=2,
        present_factor=1, target_cache_entries=512, retained_tree_policy=POLICY, primary_completion_policy=COMPLETION_POLICY,
        baseline_root=str(BASELINE), baseline_metrics_root=str(BASELINE_METRICS),
        change_only='Only B_new=B_original+ceil((1-c)*floor); continuation primary, retained branches, prices, kernel, cache, fallback and guards unchanged.',
        resources=dict(model_limit_GiB=20, audit_limit_GiB=8, metric_limit_GiB=8,
            fresh_margin_GiB=8, model_timeout_seconds=21600, audit_timeout_seconds=3600),
        metric_methods=['continued1', 'budget1'], frames=['initial', 'sketch'], metric_sets=8,
        concrete_count=1678392, concrete_k=83920, spatial_count=48194, spatial_k=20,
        metric_policy='Same exact evaluate_frame ET primary and independent Expat/histogram, complete zero-inclusive original domains, full spans/layers and lexical ties. Retained baseline both frames must match its closed all8 comparison, and both initial frames must match original certified initialization. Every candidate regression retained.',
        gate='Complete current retained A* baseline/all3audits/closed admission/all8metrics and owner gone. Prepared entry submits no queue/model; no retry or adoption.',
        timeout_policy='Terminate only this stage child after its preregistered timeout, preserve outputs and record failure; no automatic retry or partial success.',
        cost_policy='Retain all loading/authentication/construction/cache/search/report/audit/metric costs. Historical independent runs are unpaired and not continuous workflow benefit.',
        post_label_development=True, heldout=False, promoted=False, goal_complete=False))
    print('Prepared full neuron continue-after-rejection trial; no model or queue submitted.', flush=True)


def run_stage(root, name, args, limit, timeout):
    assert not any((root/(name+suffix)).exists() for suffix in ('.log', '_process.json', '_terminal.json', '_admission.json')), 'Started/ambiguous stage: no retry'
    maximum = int(Path('/sys/fs/cgroup/memory.max').read_text())
    current = int(Path('/sys/fs/cgroup/memory.current').read_text())
    admission = dict(shared_memory_max_bytes=maximum, shared_memory_current_bytes=current,
        child_limit_bytes=limit, margin_bytes=8*2**30, admitted=maximum-current>=limit+8*2**30)
    write(root/(name+'_admission.json'), admission)
    assert admission['admitted'], 'Fresh resource admission failed; stop for analysis'
    started = time.perf_counter()
    timed_out = False
    with (root/(name+'.log')).open('x') as log:
        child = subprocess.Popen([sys.executable, *map(str, args)], cwd=R,
            stdout=log, stderr=subprocess.STDOUT,
            preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (limit, limit)))
        write(root/(name+'_process.json'), dict(pid=child.pid, args=child.args,
            start_stat=Path('/proc', str(child.pid), 'stat').read_text(), address_space_limit_bytes=limit))
        print('CONTINUE PRIMARY START', name, child.pid, flush=True)
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            child.terminate()
            try:
                code = child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill()
                code = child.wait()
    terminal = dict(exit_status=code, timed_out=timed_out, seconds=time.perf_counter()-started,
                    timeout_seconds=timeout, address_space_limit_bytes=limit)
    write(root/(name+'_terminal.json'), terminal)
    assert code == 0 and not timed_out, 'Failed/timed-out stage preserved; no retry'
    return terminal


def run():
    protocol = load(OUT/'protocol.json')
    check(protocol['bindings'])
    predecessors = baseline_gate()
    write(OUT/'process.json', dict(pid=os.getpid(), start_stat=Path('/proc/self/stat').read_text(),
        args=Path('/proc/self/cmdline').read_bytes().decode().rstrip('\0').split('\0')))
    write(OUT/'launch_bindings.json', predecessors)
    model = OUT/'model'
    stages = [('model', [DRIVER, ENDPOINT, model, BASE, CRITICALITY, '1'], 20*2**30, 21600),
        ('initial_audit', [PHYSICAL_TOOL, model, 'initial', model/'initial_physical_verification.json'], 8*2**30, 3600),
        ('sketch_audit', [PHYSICAL_TOOL, model, 'sketch', model/'sketch_physical_verification.json'], 8*2**30, 3600),
        ('event_audit', [EVENT_TOOL, model, 'neuron', model/'verification.json', '1'], 8*2**30, 3600)]
    for name, args, limit, timeout in stages:
        check(protocol['bindings'])
        check(predecessors)
        run_stage(OUT, name, args, limit, timeout)
    write(OUT/'pipeline_terminal.json', dict(exit_status=0, all_stages_completed=True,
        requires_separate_closed_admission=True, quality_or_workflow_gain_proven=False))


def admit():
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 8*2**30+512*2**20, 'Fresh final-admission memory gate failed'
    resource.setrlimit(resource.RLIMIT_AS, (512*2**20, 512*2**20))
    assert gone(OUT) and load(OUT/'pipeline_terminal.json')['all_stages_completed']
    bindings = {**load(OUT/'protocol.json')['bindings'], str(OUT/'protocol.json'): sha(OUT/'protocol.json')}
    def bind(path):
        bindings[str(path)] = sha(path)
        return load(path)
    def merge(mapping):
        for path, digest in mapping.items():
            assert path not in bindings or bindings[path] == digest
            bindings[path] = digest
    bind(OUT/'pipeline_terminal.json')
    merge(bind(OUT/'launch_bindings.json'))
    resources = {}
    for name in ('model', 'initial_audit', 'sketch_audit', 'event_audit'):
        expected = (20 if name == 'model' else 8)*2**30
        terminal = bind(OUT/(name+'_terminal.json'))
        metadata = bind(OUT/(name+'_process.json'))
        admission = bind(OUT/(name+'_admission.json'))
        assert gone(OUT, name+'_process.json')
        assert terminal['exit_status'] == 0 and terminal['timed_out'] is False
        assert terminal['address_space_limit_bytes'] == metadata['address_space_limit_bytes'] == expected
        assert admission['admitted'] and admission['child_limit_bytes'] == expected and admission['margin_bytes'] == 8*2**30
        assert admission['shared_memory_max_bytes']-admission['shared_memory_current_bytes'] >= expected+8*2**30
        assert terminal['timeout_seconds'] == (21600 if name == 'model' else 3600)
        resources[name] = terminal
    model = OUT/'model'
    proofs = [bind(model/name) for name in ('initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json')]
    for proof in proofs:
        assert proof[PHYSICAL] and proof['completed'] == 77106
        merge(proof['bindings'])
    event = proofs[-1]
    assert event['events'] == event['committed']+event['retained'] == 101534
    assert event['present_factor'] == 1 and all(event[k] is True for k in EVENT_FLAGS)
    assert event['complete_primary_search_after_rejection_and_isolated_witnesses_pass'] is True
    assert proofs[1]['overflow_units'] == event['overflow_units']
    candidate, baseline = bind(model/'protocol.json'), bind(BASELINE/'model/protocol.json')
    assert candidate['retained_tree_policy'] == baseline['retained_tree_policy'] == POLICY
    assert candidate['primary_completion_policy'] == COMPLETION_POLICY
    audit_protocol(candidate,baseline)
    for name in ('initial.json', 'floors.json', 'round0.json', 'round1.json', 'sketch.json'):
        bindings[str(model/name)] = sha(model/name)
        if name in ('initial.json', 'floors.json'):
            bindings[str(BASELINE/'model'/name)] = sha(BASELINE/'model'/name)
            if name=='floors.json':assert bindings[str(model/name)] == bindings[str(BASELINE/'model'/name)]
    pins_path=CRITICALITY/'initial_connection_criticalities.json'
    bindings[str(pins_path)]=sha(pins_path)
    parity=audit_initial_parity(load(model/'initial.json'),load(BASELINE/'model/initial.json'),load(pins_path))
    assert parity['connections']==77106
    receipt = model/'receipt.json'
    bindings[str(receipt)] = sha(receipt)
    counts, rounds = {}, []
    query_cids = defaultdict(set)
    for query in load(ENDPOINT)['connections']:
        query_cids[query['net_id']].add(query['connection_id'])
    for kind, index, item in round_items(receipt):
        if kind == 'event':
            kept = set(item['retained_connection_ids'])
            searched = set(item['primary_search_connection_ids'])
            assert not kept & searched and kept | searched == query_cids[item['net_id']]
            assert len(kept) == len(item['retained_connection_ids']) and len(searched) == len(item['primary_search_connection_ids'])
            assert all(row['connection_id'] in searched for row in item['primary_rejected_expansions'])
            assert len(item['primary_search_connection_ids']) == item['primary_search_calls']
            counts[index] = counts.get(index, 0)+1
        else:
            assert counts[index] == len(item['affected_nets']) == 50767
            rounds.append(index)
    assert rounds == [0, 1] and sum(counts.values()) == 101534
    check(bindings)
    write(OUT/'independent_final_admission_v1.json', dict(all_pass=True, bindings=bindings,
        all_original_connections=77106, all_events=101534, all_three_independent_audits_pass=True,
        all_primary_coverage_and_isolated_rejection_audits_pass=True, initial_paths_and_ledgers_preserved_floors_byte_identical=True, budget_parity=parity,
        protocol_unchanged_except_registered_budget_policy=True,
        stage_resources_and_terminals=resources, overflow_units=event['overflow_units'],
        quality_or_workflow_gain_proven=False, promoted=False))
    print('PASS complete closed continue-after-rejection trial admission.', flush=True)


def metrics():
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 16*2**30, 'Fresh metric memory gate failed'
    resource.setrlimit(resource.RLIMIT_AS, (8*2**30, 8*2**30))
    baseline_bindings = baseline_gate()
    admission = load(OUT/'independent_final_admission_v1.json')
    assert admission['all_pass'] and gone(OUT)
    check(admission['bindings'])
    protocol = load(OUT/'protocol.json')
    check(protocol['bindings'])
    result_root = OUT/'metrics'
    result_root.mkdir()
    bindings = dict(protocol['bindings'])
    def merge(mapping):
        for path, digest in mapping.items():
            assert path not in bindings or bindings[path] == digest
            bindings[path] = digest
    merge(baseline_bindings)
    merge(admission['bindings'])
    bindings[str(OUT/'independent_final_admission_v1.json')] = sha(OUT/'independent_final_admission_v1.json')
    def bind(path):
        digest = sha(path)
        assert str(path) not in bindings or bindings[str(path)] == digest
        bindings[str(path)] = digest
        return load(path)
    accepted = bind(REFERENCE/'label_admission.json')
    assert accepted['label_accepted']
    merge(accepted['bindings'])
    truth_path = R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json'
    assert str(truth_path) in accepted['bindings']
    truth = bind(truth_path)['node_occupancy']
    graph = Path(load(ENDPOINT)['inputs']['graph']['path'])
    assert str(graph) in bindings
    baseline_metrics = bind(BASELINE_METRICS/'verification.json')['metrics']['continued1']
    archived = bind(REFERENCE/'prediction_metrics.json')['metrics']['initial']
    check(bindings)
    write(result_root/'evaluation_started.json', dict(address_space_limit_bytes=8*2**30,
        shared_headroom_bytes=free, margin_bytes=8*2**30,
        methods=protocol['metric_methods'], full_metric_sets=8))
    started = time.perf_counter()
    results = {}
    for method, root in (('continued1', BASELINE), ('budget1', OUT)):
        frames = {}
        for frame in ('initial', 'sketch'):
            state = bind(root/'model'/(frame+'.json'))
            assert state['completed_connections'] == state['required_connections'] == 77106
            ledger = state['ledger']
            del state
            gc.collect()
            row = evaluate_frame(graph, ledger, truth)
            assert sum(row['original_node_counts'].values()) == 3593250
            for domain, size, k in (('concrete', 1678392, 83920), ('spatial', 48194, 20)):
                assert row['metrics'][domain]['universe_size'] == size and row['metrics'][domain]['k'] == k
            if method == 'continued1':
                assert row['metrics'] == baseline_metrics[frame]['metrics']
            if frame == 'initial':
                assert row['metrics'] == {k: archived[k] for k in ('concrete', 'spatial')}
            frames[frame] = row
            del ledger
            gc.collect()
        results[method] = frames
        write(result_root/(method+'_metrics.json'), frames)
    check(bindings)
    write(result_root/'verification.json', dict(all_pass=True, bindings=bindings, metrics=results,
        independently_checked_metric_sets=8, methods=protocol['metric_methods'],
        evaluation_seconds=time.perf_counter()-started,
        peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        post_label_development=True, heldout=False, promoted=False,
        paired_or_continuous_workflow_gain_proven=False))
    print('PASS all8 full continue-after-rejection causal development metrics; interpretation required.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run', 'admit', 'metrics'))
    args = parser.parse_args()
    globals()[args.action]()
