"""Frozen full-domain baseline/candidate metrics; no model submissions."""
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
from run_neuron_quotient_astar_pipeline_v1 import BASELINE, OUT as CANDIDATE, gone, PHYSICAL, EVENT_FLAGS

OUT = R/'experiments/neuron_quotient_astar_full_comparison_v1_2026-10-17'
REFERENCE = R/'experiments/neuron_certified_native_metrics_v1_2026-10-15'
MODELS = dict(baseline1=BASELINE, candidate1=CANDIDATE)


def load(path):
    return json.loads(Path(path).read_text())


def check(bindings):
    assert all(sha(p) == h for p, h in bindings.items())


def prepare():
    bindings = closure([Path(__file__)])
    for path in (CANDIDATE/'protocol.json', REFERENCE/'label_admission.json',
                 REFERENCE/'prediction_metrics.json', BASELINE/'independent_final_admission_v1.json',
                 R/'experiments/neuron_scaled_metric_comparison_contract_v1_2026-10-15/verification.json'):
        bindings[str(path)] = sha(path)
    assert load(REFERENCE/'label_admission.json')['label_accepted']
    assert load(BASELINE/'independent_final_admission_v1.json')['all_pass']
    check(bindings)
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        methods=['baseline1', 'candidate1'], present_factor=1, cache_entries=512,
        frames=['initial', 'sketch'], independently_checked_metric_sets=8,
        concrete_channel_count=1678392, concrete_k=83920,
        spatial_bin_count=48194, spatial_k=20,
        metric_policy='Frozen original complete zero-inclusive positive-capacity CHANX/CHANY domain, full spans/layers, lexical string ID ties; concrete ceil(N/20), spatial20. Same existing evaluate_frame ET primary and independent Expat/histogram-rank/MAE/top-k verification. Report every regression.',
        baseline_policy='Both baseline1 frames and candidate initial must exactly reproduce archived certified factor1 metrics. Candidate final may differ and must be reported without selection.',
        required='Candidate full original77106connections/101534events/all3 independent audits and owner gone. No model launch/retry, partial-frame acceptance, factor or label selection.',
        known_label_development=True, heldout=False, promoted=False,
        native_candidate_rerouting=False, paired_or_full_workflow_gain_proven=False), indent=2)+'\n')
    print('Prepared baseline/candidate all8 metric sets; evaluation not launched.', flush=True)


def run():
    start = time.perf_counter()
    protocol = load(OUT/'protocol.json')
    check(protocol['bindings'])
    assert load(CANDIDATE/'pipeline_terminal.json')['all_stages_completed']
    assert gone(CANDIDATE), 'Candidate owner not confirmed gone'
    assert not (OUT/'evaluation_started.json').exists(), 'Ambiguous restart refused'
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 16*2**30
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
    for method, root in MODELS.items():
        assert bind(root/'pipeline_terminal.json')['all_stages_completed']
        assert bind(root/'model/protocol.json')['present_factor'] == 1
        for name in ('initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json'):
            proof = bind(root/'model'/name)
            assert proof[PHYSICAL] and proof['completed'] == 77106
            merge(proof['bindings'])
            if name == 'verification.json':
                assert proof['present_factor'] == 1 and proof['events'] == 101534
                assert all(proof[k] for k in EVENT_FLAGS)
    native = bind(REFERENCE/'label_admission.json')
    assert native['label_accepted']
    merge(native['bindings'])
    truth_path = R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json'
    assert str(truth_path) in native['bindings']
    truth = bind(truth_path)['node_occupancy']
    command = bind(R/'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json')['native_command']
    graph = Path(command[command.index('--read_rr_graph')+1])
    assert str(graph) in bindings
    archived = bind(REFERENCE/'prediction_metrics.json')['metrics']
    check(bindings)
    with (OUT/'evaluation_started.json').open('x') as stream:
        json.dump(dict(shared_headroom_bytes=free, address_space_limit_bytes=8*2**30), stream)
    results = {}
    for method, root in MODELS.items():
        frames = {}
        for frame in protocol['frames']:
            state = bind(root/'model'/(frame+'.json'))
            assert state['completed_connections'] == state['required_connections'] == 77106
            ledger = state['ledger']
            del state
            gc.collect()
            row = evaluate_frame(graph, ledger, truth)
            assert sum(row['original_node_counts'].values()) == 3593250
            assert row['metrics']['concrete']['universe_size'] == 1678392
            assert row['metrics']['concrete']['k'] == 83920
            assert row['metrics']['spatial']['universe_size'] == 48194
            assert row['metrics']['spatial']['k'] == 20
            if method == 'baseline1' or frame == 'initial':
                assert row['metrics'] == {key: archived[frame][key] for key in ('concrete', 'spatial')}
            frames[frame] = row
            del ledger
            gc.collect()
        results[method] = frames
        with (OUT/(method+'_metrics.json')).open('x') as stream:
            json.dump(frames, stream, indent=2)
            stream.write('\n')
    check(bindings)
    value = dict(all_pass=True, bindings=bindings, metrics=results,
        independently_checked_metric_sets=8, present_factor=1, cache_entries=512,
        evaluation_seconds=time.perf_counter()-start,
        peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        known_label_development=True, heldout=False, promoted=False,
        paired_performance_or_full_workflow_gain_proven=False)
    with (OUT/'verification.json').open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    print('PASS all8 metric sets; research interpretation still required.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'run'))
    args = parser.parse_args()
    globals()[args.action]()
