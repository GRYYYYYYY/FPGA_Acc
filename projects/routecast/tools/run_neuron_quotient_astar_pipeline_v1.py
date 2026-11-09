"""Frozen factor1/cache512 full candidate; explicit run after predecessor closure.

Preparation launches nothing. No recovery, retries or factor selection.
"""
import argparse
import datetime
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from observe_neuron_scaled_present_pipeline_v1 import process
from verify_neuron_scaled_present_final_v1 import EVENT_FLAGS, PHYSICAL

OUT = R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17'
BASELINE = R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15'
DIAGNOSTIC = R/'experiments/neuron_quotient_cache512_construction_v1_2026-10-17'
MODEL_QUEUE = R/'experiments/neuron_scaled_present_recovery_v1_2026-10-17'
METRIC_QUEUE = R/'experiments/neuron_scaled_metric_followup_v3_2026-10-17'
METRICS = R/'experiments/neuron_scaled_present_full_comparison_v2_2026-10-17'
DRIVER = R/'tools/run_design_scoped_quotient_astar_retained_tree_v2.py'
PHYSICAL_TOOL = R/'tools/verify_resident_demand_frame_direct_lattice_v7.py'
EVENT_TOOL = R/'tools/verify_scaled_present_retained_tree_full_schedule_v1.py'
ENDPOINT = R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
BASE = R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json'
CRITICALITY = R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality'


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def check(bindings):
    assert all(sha(p) == h for p, h in bindings.items()), 'Frozen binding drift'


def gone(root, metadata='process.json'):
    m = load(root/metadata)
    state = process(m['pid'], int(m['start_stat'].rsplit(')', 1)[1].split()[19]))
    return state.get('status') == 'missing_not_terminal_evidence' or state.get('verified_identity') is False or state.get('state') in ('Z', 'X')


def prepare():
    contract = R/'experiments/quotient_cache512_factory_contract_v2_2026-10-17/verification.json'
    assert load(contract)['all_pass']
    check(load(contract)['bindings'])
    bindings = closure([Path(__file__), DRIVER, PHYSICAL_TOOL, EVENT_TOOL])
    for p in (contract, ENDPOINT, BASE, CRITICALITY/'verification.json',
              BASELINE/'independent_final_admission_v1.json', BASELINE/'model/initial.json',
              BASELINE/'model/floors.json', DIAGNOSTIC/'protocol.json',
              R/'experiments/neuron_quotient_cache_shape_v1_2026-10-17/independent_verification.json'):
        bindings[str(p)] = sha(p)
    check(bindings)
    OUT.mkdir()
    write(OUT/'protocol.json', dict(bindings=bindings,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        original_nodes=3593250, original_edges=39165143, connections=77106,
        nets=50767, rounds=2, present_factor=1, cache_entries=512, group_pitch=4,
        hypothesis='Test complete exact quotient A* software candidate at fixed factor1/cache512 on the original exposed neuron design, retaining complete quality and total model construction costs.',
        fixed_before_original_factor_comparison=True,
        scope='Known-label development candidate; equal-score A* ties may change paths and feedback. Initial/floors must equal original factor1. Full final state/event parity is diagnostic, not a required or assumed outcome.',
        retained_primary_fanout=16, whole_NET_fallback_and_both_guards_unchanged=True,
        native_route_labels_used_by_model=False, heldout=False, promoted=False,
        predecessor_gate='Original recovery and postprocessing queues terminal0 and owners gone; all12 original factor metrics complete; static diagnostic terminal0 and owner gone, all455 tables checked, no graph searches. No model is launched by preparation.',
        required_audits=['initial original XML/Fraction physical audit', 'sketch original XML/Fraction physical audit', 'all101534 original NET transaction/objective/epoch/fallback events'],
        resources=dict(model_limit_GiB=20, audit_limit_GiB=8, fresh_margin_GiB=8),
        full_quality_policy=dict(frames=['initial', 'sketch'], methods=['baseline1', 'candidate1'],
            concrete_count=1678392, concrete_k=83920, spatial_count=48194, spatial_k=20,
            metrics=['Spearman', 'precision', 'recall', 'MAE'],
            domain='Same frozen neuron labels, complete zero-inclusive original resource domains, lexical string ties, full channel spans; ET primary plus independent Expat/histogram audit. All8 metric sets, every regression retained.'),
        cost_policy='Report complete process/stage times including loading/authentication/grouping/quotient/native workspace/cache/accounting/audits. Baseline historical sample is unpaired; no elapsed improvement or complete workflow benefit claim from local scans or one model comparison.',
        larger_goal_remaining=['strict unseen-family validation', 'native candidate route failure/RRR/wirelength/CPD', 'paired continuous full-workflow net benefit', 'full hardware/RTL/board evidence']))
    print('PREPARED only; no model or follow-up queue submitted.', flush=True)


def predecessor_bindings():
    assert load(MODEL_QUEUE/'terminal.json')['exit_status'] == 0 and gone(MODEL_QUEUE)
    assert load(METRIC_QUEUE/'terminal.json')['comparison_completed'] is True
    assert load(METRIC_QUEUE/'terminal.json')['exit_status'] == 0 and gone(METRIC_QUEUE)
    comparison = load(METRICS/'verification.json')
    assert comparison['all_pass'] and comparison['independently_checked_metric_sets'] == 12
    assert comparison['factors'] == [1, 2, 4] and comparison['promoted'] is False
    assert load(DIAGNOSTIC/'terminal.json')['exit_status'] == 0 and gone(DIAGNOSTIC)
    diagnostic = load(DIAGNOSTIC/'verification.json')
    assert diagnostic['all_pass'] and diagnostic['all_endpoint_target_tables'] == 455
    assert diagnostic['graph_search_calls'] == 0
    check(comparison['bindings'])
    check(diagnostic['bindings'])
    return {str(p): sha(p) for p in (MODEL_QUEUE/'terminal.json', METRIC_QUEUE/'terminal.json',
        METRICS/'verification.json', DIAGNOSTIC/'terminal.json', DIAGNOSTIC/'verification.json')}


def run():
    protocol = load(OUT/'protocol.json')
    check(protocol['bindings'])
    bindings = {**protocol['bindings'], **predecessor_bindings(), str(OUT/'protocol.json'): sha(OUT/'protocol.json')}
    # An exclusive owner record refuses ambiguous resubmission even after failure.
    write(OUT/'process.json', dict(pid=os.getpid(), start_stat=Path('/proc/self/stat').read_text(),
        args=Path('/proc/self/cmdline').read_bytes().decode().rstrip('\0').split('\0')))
    write(OUT/'launch_bindings.json', bindings)
    model = OUT/'model'
    stages = [('model', 20, [DRIVER, ENDPOINT, model, BASE, CRITICALITY, '1']),
        ('initial_audit', 8, [PHYSICAL_TOOL, model, 'initial', model/'initial_physical_verification.json']),
        ('sketch_audit', 8, [PHYSICAL_TOOL, model, 'sketch', model/'sketch_physical_verification.json']),
        ('event_audit', 8, [EVENT_TOOL, model, 'neuron', model/'verification.json', '1'])]
    for name, gib, args in stages:
        check(bindings)
        limit = gib*2**30
        maximum = int(Path('/sys/fs/cgroup/memory.max').read_text())
        current = int(Path('/sys/fs/cgroup/memory.current').read_text())
        admission = dict(shared_memory_max_bytes=maximum, shared_memory_current_bytes=current,
            child_limit_bytes=limit, margin_bytes=8*2**30, admitted=maximum-current>=limit+8*2**30)
        write(OUT/(name+'_admission.json'), admission)
        assert admission['admitted'], 'Memory gate failed; no retry'
        tick = time.perf_counter()
        with (OUT/(name+'.log')).open('x') as log:
            child = subprocess.Popen([sys.executable, *map(str, args)], cwd=R, stdout=log,
                stderr=subprocess.STDOUT, preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS, (limit, limit)))
            write(OUT/(name+'_process.json'), dict(pid=child.pid, args=child.args,
                start_stat=Path('/proc', str(child.pid), 'stat').read_text(), address_space_limit_bytes=limit))
            print('NEURON QUOTIENT START', name, child.pid, flush=True)
            code = child.wait()
        write(OUT/(name+'_terminal.json'), dict(exit_status=code, seconds=time.perf_counter()-tick,
            address_space_limit_bytes=limit))
        assert code == 0, f'Stage {name} failed; no retry'
    check(bindings)
    for frame in ('initial.json', 'floors.json'):
        assert sha(model/frame) == sha(BASELINE/'model'/frame)
    proof_bindings = dict(bindings)
    audits = [load(model/name) for name in ('initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json')]
    for proof in audits:
        assert proof[PHYSICAL] is True and proof['completed'] == 77106
        for path, digest in proof['bindings'].items():
            assert path not in proof_bindings or proof_bindings[path] == digest
            proof_bindings[path] = digest
    events = audits[-1]
    assert events['events'] == events['committed']+events['retained'] == 101534
    assert events['present_factor'] == 1 and all(events[k] is True for k in EVENT_FLAGS)
    assert audits[1]['overflow_units'] == events['overflow_units']
    check(proof_bindings)
    write(OUT/'pipeline_terminal.json', dict(exit_status=0, all_stages_completed=True,
        all_three_independent_audits_pass=True, all_original_connections=77106, full_NET_events=101534,
        initial_and_floors_byte_identical=True, final_overflow=events['overflow_units'], promoted=False))
    print('PASS complete neuron candidate and all3 audits; quality and final metadata admission remain required.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    args = parser.parse_args()
    globals()[args.action]()
