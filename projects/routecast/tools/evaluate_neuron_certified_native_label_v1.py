"""Admit complete original native truth with explicit output-fanout certificates.

The scientific/native settings and metric protocol stay frozen. The old
ignored-only implementation rejection is preserved, with the additional source
realization proof recorded as a post-label semantic implementation extension.
"""
import gc
import json
from pathlib import Path
import resource
import sys
import time

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_NET_occupancy_v1 import occupancy
from neuron_complete_prediction_metrics_v1 import evaluate


def main():
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    tick=time.perf_counter()
    src=R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15'
    cross=R/'experiments/neuron_output_crossbar_realization_v1_2026-10-15'
    native=R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14'
    model=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13/model'
    policy=R/'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json'
    load=lambda p:json.loads(p.read_text())
    output=R/'experiments/neuron_certified_native_metrics_v1_2026-10-15'
    proofs=[src/'physical_verification.json',cross/'verification.json',cross/'independent_verification.json',
            cross/'input_pin_verification.json']
    values=[load(p) for p in proofs]
    physical,generated,review,inputs=values
    assert physical['complete_native_demand_pass'] and physical['connections']==77106 and physical['overflow_units']==0
    assert generated['all_pass'] and review['all_pass'] and inputs['all_pass']
    assert generated['all_native_mismatch_records_exhaustively_reproduced']
    assert review['all_crossbar_OPINs_roots_classes_modes_drivers_and_complete_fanout_pass']
    assert review['full_original_physical_trace_digests_identical'] and review['all_native_mismatch_records_reproduced']
    assert review['SDC_byte_identical'] and review['native_FULL_and_STA_pass'] and review['packed_netlist_byte_identical']
    assert len(review['invalid_certificate_rejections'])==5
    assert inputs['nonignored_sink_pins']==77106 and inputs['all_input_and_clock_NET_tokens_identical']
    assert load(native/'terminal.json')['exit_status']==0 and load(native/'input_postcheck.json')['all_inputs_unchanged']
    assert sha(policy)==load(native/'launch.json')['prereg_sha256']
    bindings=closure([Path(__file__)])
    for p,v in zip(proofs,values):
        bindings[str(p)]=sha(p)
        for q,h in v['bindings'].items():
            assert q not in bindings or bindings[q]==h
            bindings[q]=h
    for p in [policy,native/'terminal.json',native/'launch.json',native/'input_postcheck.json']:
        bindings[str(p)]=sha(p)
    for p,h in bindings.items(): assert sha(p)==h,p
    current=int(Path('/sys/fs/cgroup/memory.current').read_text())
    maximum=int(Path('/sys/fs/cgroup/memory.max').read_text())
    assert maximum-current>=16*2**30,'Need 8 GiB process allowance plus 8 GiB shared margin'
    output.mkdir(exist_ok=False)
    admission=dict(bindings=bindings,label_accepted=True,original_connections=77106,original_routed_NETs=50767,
                   original_frozen_native_and_metric_protocol=str(policy),
                   original_native_inputs_settings_and_physical_route_unchanged=True,
                   old_ignored_only_implementation_gate_pass=False,
                   original_gate_failure_preserved=str(src/'canonical_failure.json'),
                   semantic_implementation_extension_after_label=True,
                   semantic_extension='All actual output pins, including multi-OPIN NETs, independently bound to their unchanged original packed atom driver through an original complete crossbar. All 68217 output mismatches exactly replayed; remaining 37 pins authenticated ignored. All packed input and clock NET tokens, native FULL/STA, SDC, and physical sequences checked.',
                   acceptance_requirements=dict(native_exit0_and_FULL=True,complete_original_XML_physical_and_capacity=True,
                       exact_complete_nonignored_demand=True,complete_packed_output_driver_and_fanout_semantics=True,
                       all_input_clock_and_ignored_pin_semantics=True,canonical_physical_trace_and_SDC_and_native_STA=True),
                   shared_memory_current_bytes=current,shared_memory_max_bytes=maximum,
                   heldout_family_certified=False,
                   scope='Complete frozen neuron native cold truth admitted for descriptive development metrics with explicit post-label semantic implementation adaptation. Old narrower gate still fails. No prospective validation of this adaptation, original HDL functional equivalence, heldout or end-to-end gain claim.')
    (output/'label_admission.json').write_text(json.dumps(admission,indent=2)+'\n')
    print('NATIVE LABEL ADMITTED WITH EXPLICIT COMPLETE OUTPUT-FANOUT CERTIFICATE',flush=True)
    frames=[]
    for name in ['initial','sketch']:
        frame=load(model/(name+'.json'))
        assert frame['completed_connections']==frame['required_connections']==77106
        frames.append(frame['ledger']);del frame
    gc.collect()
    truth,NETs=occupancy(native/'output.route')
    assert truth==load(src/'physical_audit.json')['node_occupancy']
    graph=Path(load(policy)['native_command'][load(policy)['native_command'].index('--read_rr_graph')+1])
    metric_tick=time.perf_counter()
    result=evaluate(graph,frames[0],frames[1],truth)
    metric_seconds=time.perf_counter()-metric_tick
    result.update(bindings=bindings,label_admission=str(output/'label_admission.json'),
                  label_admission_sha256=sha(output/'label_admission.json'),
                  original_graph_sha256=sha(graph),native_qor=physical['native_qor'],
                  semantic_implementation_extension_after_label=True,
                  metric_evaluation_seconds=metric_seconds,whole_evaluator_seconds=time.perf_counter()-tick,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    for p,h in bindings.items(): assert sha(p)==h,p
    (output/'prediction_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    pipeline=model.parent
    phase_paths=[R/'experiments/titan23_neuron_preroute_v1_2026-10-13/pack_terminal.json',
                 R/'experiments/titan23_neuron_preroute_v1_2026-10-13/place_terminal.json',
                 R/'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/graph_terminal.json',
                 R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/indexed/terminal.json',
                 R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/terminal.json',
                 *[pipeline/(s+'_terminal.json') for s in ['model','initial_audit','sketch_audit','event_audit']],
                 native/'terminal.json',src/'physical_terminal.json',
                 R/'experiments/titan23_neuron_native_label_audit_v1_2026-10-15/physical_failure.json',
                 src/'canonical_failure.json']
    phases=[]
    for p in phase_paths:
        d=load(p);seconds=d.get('seconds',d.get('process_seconds'))
        assert seconds is not None
        phases.append(dict(receipt=str(p),sha256=sha(p),seconds=seconds,
                           exit_status=d.get('exit_status'),scope='Archived complete process observation; failures retained. Nested observations are not additive.'))
    for p in [cross/'verification.json',cross/'independent_verification.json',cross/'input_pin_verification.json']:
        phases.append(dict(receipt=str(p),sha256=sha(p),seconds=load(p)['seconds'],scope='New complete semantic certificate stage.'))
    compact=R/'experiments/titan23_neuron_compact_graph_admission_v1_2026-10-13/verification.json'
    d=load(compact)
    phases.append(dict(receipt=str(compact),sha256=sha(compact),graph_conversion_load_seconds=d['load_seconds'],
                       independent_graph_audit_seconds=d['audit_seconds'],scope='Historical standalone conversion/admission, also repeated inside later model process; not additive.'))
    rr=R/'experiments/titan23_neuron_graph_recovery_v1_2026-10-13/receipt.json'
    phases.append(dict(receipt=str(rr),sha256=sha(rr),endpoint_extraction_seconds=load(rr)['rows'][0]['extraction_seconds']))
    costs=dict(observations=phases,metric_evaluation_seconds=metric_seconds,whole_evaluator_seconds=time.perf_counter()-tick,
               observations_not_additive=True,complete_end_to_end_total_available=False,
               explicitly_unmeasured_phases=['Original archive acquisition/copy/hash operations','All build and wide-node-base conversion costs','Failed one-OPIN serialization precondition diagnostic elapsed time','Historical recovery and duplicated capture stages not all timed'],
               speedup_or_end_to_end_benefit_claim=False,
               scope='Per-stage observations include model, native routing, independent audits and failures. Missing historical timings remain explicit; no total or paired speedup is inferred.')
    (output/'phase_costs.json').write_text(json.dumps(costs,indent=2)+'\n')
    (output/'terminal.json').write_text(json.dumps(dict(exit_status=0,seconds=time.perf_counter()-tick,
          peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
    print(json.dumps(result['metrics'],indent=2),flush=True)


if __name__=='__main__':main()
