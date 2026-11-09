"""All-factor known-label development comparison; no model submissions or selection."""
import argparse
import datetime
import gc
import json
import resource
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from neuron_scaled_present_frame_metrics_v1 import evaluate_frame
from observe_neuron_scaled_present_pipeline_v1 import process

OUT = R/'experiments/neuron_scaled_present_full_comparison_v1_2026-10-15'
REFERENCE = R/'experiments/neuron_certified_native_metrics_v1_2026-10-15'
QUEUE = R/'experiments/neuron_scaled_present_followup_v1_2026-10-15'


def load(path):
    return json.loads(path.read_text())


def case(factor):
    return R/f'experiments/titan23_neuron_scaled_present_factor{factor}_pipeline_v1_2026-10-15'


def check(bindings):
    for path, digest in bindings.items():
        assert sha(path) == digest, ('binding changed', path)


def owner_gone(state):
    if state.get('status') == 'missing_not_terminal_evidence':
        return True
    if state.get('verified_identity') is False and type(state.get('startticks')) is int:
        return True  # PID exists with a different recorded start identity.
    return state.get('verified_identity') is True and state.get('state') in ('Z', 'X')


def prepare():
    bindings = closure([Path(__file__)])
    for path in (REFERENCE/'label_admission.json', REFERENCE/'prediction_metrics.json',
                 REFERENCE/'hotspot_diagnosis.json',
                 R/'experiments/neuron_scaled_present_ablation_prereg_v1_2026-10-15/protocol.json',
                 case(1)/'independent_final_admission_v1.json',
                 R/'experiments/neuron_scaled_metric_comparison_contract_v1_2026-10-15/verification.json'):
        bindings[str(path)] = sha(path)
    assert load(REFERENCE/'label_admission.json')['label_accepted'] is True
    assert load(case(1)/'independent_final_admission_v1.json')['all_pass'] is True
    assert load(R/'experiments/neuron_scaled_metric_comparison_contract_v1_2026-10-15/verification.json')['all_pass'] is True
    check(bindings)
    protocol = dict(bindings=bindings, created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    factors=[1, 2, 4], frames=['initial', 'sketch'], development_only=True,
                    known_native_labels=True, post_label_hypothesis=True, heldout=False,
                    concrete_channel_count=1678392, concrete_k=83920,
                    spatial_bin_count=48194, spatial_k=20,
                    metric_policy='Complete original positive-capacity CHANX/CHANY IDs, zero occupancy included; concrete k=ceil(N/20), spatial k=20; lexical string resource ID ties; preserve layer and full channel spans. Report Spearman, top-k precision/recall and MAE for every factor/frame, including regressions.',
                    verification='Primary ElementTree domain and existing compare; independent complete Expat aggregation and histogram-rank/MAE/top-k check for each frame. Factor1 and every initial frame must exactly reproduce certified archived metrics. Tie sensitivity is diagnostic, never a replacement metric.',
                    required='All factors independently terminal-admitted, each 77106 connections/101534 events; original queue completed and owner gone. Fresh8GiB+8GiB memory admission before full comparison.',
                    performance='Complete stage receipts and evaluator duration reported separately; no summation into a continuous workflow or paired benefit.',
                    promotion_allowed=False, native_candidate_rerouting=False,
                    scope='Frozen known-label neuron development evaluation entry only. This preparation is not executed large-factor metrics or full research completion.')
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    print('Prepared frozen complete factor1/2/4 development metric comparison; full evaluation not launched.')


def run():
    tick = time.perf_counter()
    protocol = load(OUT/'protocol.json')
    check(protocol['bindings'])
    assert not (OUT/'evaluation_started.json').exists(), 'No ambiguous restart/adoption'
    terminal = load(QUEUE/'terminal.json')
    assert terminal['exit_status'] == 0 and terminal['all_planned_followup_factors_completed'] is True
    owner = load(QUEUE/'process.json')
    start = int(owner['start_stat'].rsplit(')', 1)[1].split()[19])
    state = process(owner['pid'], start)
    assert owner_gone(state), 'Queue owner not confirmed gone'
    free = int(Path('/sys/fs/cgroup/memory.max').read_text()) - int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 16*2**30, 'Full metric evaluation deferred by shared memory admission'
    resource.setrlimit(resource.RLIMIT_AS, (8*2**30, 8*2**30))
    bindings = {**protocol['bindings'], str(OUT/'protocol.json'): sha(OUT/'protocol.json')}

    def bind(path):
        digest = sha(path)
        assert str(path) not in bindings or bindings[str(path)] == digest
        bindings[str(path)] = digest
        return load(path)

    def merge(mapping):
        for path, digest in mapping.items():
            assert path not in bindings or bindings[path] == digest
            bindings[path] = digest

    bind(QUEUE/'terminal.json')
    resources = {}
    for factor in protocol['factors']:
        admission = bind(case(factor)/'independent_final_admission_v1.json')
        assert admission['all_pass'] is True and admission['present_factor'] == factor
        assert admission['all_original_connections'] == 77106 and admission['all_events'] == 101534
        assert admission['all_three_independent_audits_pass'] is True
        merge(admission['bindings'])
        resources[str(factor)] = admission['stage_resources_and_terminals']
    native = bind(REFERENCE/'label_admission.json')
    assert native['label_accepted'] is True
    merge(native['bindings'])
    truth_path = R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json'
    assert str(truth_path) in native['bindings']
    truth = bind(truth_path)['node_occupancy']
    policy = bind(R/'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json')
    command = policy['native_command']
    graph = Path(command[command.index('--read_rr_graph')+1])
    assert str(graph) in bindings
    archived = bind(REFERENCE/'prediction_metrics.json')['metrics']
    check(bindings)
    (OUT/'evaluation_started.json').write_text(json.dumps(dict(shared_headroom_bytes=free, address_space_limit_bytes=8*2**30, margin_bytes=8*2**30))+'\n')
    results = {}
    for factor in protocol['factors']:
        frames = {}
        for frame in protocol['frames']:
            path = case(factor)/'model'/(frame+'.json')
            value = bind(path)
            assert value['completed_connections'] == value['required_connections'] == 77106
            ledger = value['ledger']
            del value
            gc.collect()
            row = evaluate_frame(graph, ledger, truth)
            assert sum(row['original_node_counts'].values()) == 3593250
            assert row['metrics']['concrete']['universe_size'] == protocol['concrete_channel_count']
            assert row['metrics']['concrete']['k'] == protocol['concrete_k']
            assert row['metrics']['spatial']['universe_size'] == protocol['spatial_bin_count']
            assert row['metrics']['spatial']['k'] == protocol['spatial_k']
            if factor == 1 or frame == 'initial':
                assert row['metrics'] == {key: archived[frame][key] for key in ('concrete', 'spatial')}
            frames[frame] = row
            del ledger
            gc.collect()
        results[str(factor)] = frames
        with (OUT/f'factor{factor}_metrics.json').open('x') as stream:
            json.dump(frames, stream, indent=2)
            stream.write('\n')
    check(bindings)
    value = dict(bindings=bindings, all_pass=True, factors=[1, 2, 4], metrics=results,
                 independently_checked_metric_sets=12, stage_resources_and_terminals=resources,
                 evaluation_seconds=time.perf_counter()-tick,
                 peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 known_label_development=True, heldout=False, promoted=False,
                 paired_performance_or_full_workflow_gain_proven=False,
                 scope='All complete development factors reported under frozen full-domain metrics and independent aggregation. No factor selection, unseen-family, native candidate QoR, continuous workflow or hardware benefit claimed.')
    with (OUT/'verification.json').open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print('PASS all12 metric sets; complete known-label development comparison only.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    args = parser.parse_args()
    globals()[args.action]()
