"""Closed full candidate admission, separate from its submission controller."""
import json
import resource
import sys
import time
from pathlib import Path

from run_neuron_quotient_astar_pipeline_v1 import OUT, BASELINE, R, gone, EVENT_FLAGS, PHYSICAL
from compare_complete_receipt_events_stream_v1 import round_items

sys.path.insert(0, str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    started = time.perf_counter()
    free = int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free >= 8*2**30+512*2**20
    resource.setrlimit(resource.RLIMIT_AS, (512*2**20, 512*2**20))
    assert gone(OUT), 'Candidate controller still live/unknown'
    bindings = closure([Path(__file__)])
    def bind(path):
        path = Path(path)
        digest = sha(path)
        assert str(path) not in bindings or bindings[str(path)] == digest
        bindings[str(path)] = digest
        return json.loads(path.read_text())
    def merge(mapping):
        for path, digest in mapping.items():
            assert path not in bindings or bindings[path] == digest
            bindings[path] = digest
    protocol = bind(OUT/'protocol.json')
    merge(protocol['bindings'])
    assert (protocol['connections'], protocol['nets'], protocol['rounds'], protocol['present_factor'], protocol['cache_entries']) == (77106, 50767, 2, 1, 512)
    terminal = bind(OUT/'pipeline_terminal.json')
    assert terminal['exit_status'] == 0 and terminal['all_stages_completed']
    assert terminal['all_three_independent_audits_pass'] and terminal['full_NET_events'] == 101534
    resources = {}
    for stage in ('model', 'initial_audit', 'sketch_audit', 'event_audit'):
        expected = (20 if stage == 'model' else 8)*2**30
        process = bind(OUT/(stage+'_process.json'))
        admission = bind(OUT/(stage+'_admission.json'))
        stage_terminal = bind(OUT/(stage+'_terminal.json'))
        assert gone(OUT, stage+'_process.json')
        assert stage_terminal['exit_status'] == 0
        assert process['address_space_limit_bytes'] == stage_terminal['address_space_limit_bytes'] == expected
        assert admission['admitted'] and admission['child_limit_bytes'] == expected
        assert admission['margin_bytes'] == 8*2**30
        assert admission['shared_memory_max_bytes']-admission['shared_memory_current_bytes'] >= expected+8*2**30
        resources[stage] = stage_terminal
    model = OUT/'model'
    proofs = [bind(model/name) for name in ('initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json')]
    for proof in proofs:
        assert proof[PHYSICAL] is True and proof['completed'] == 77106
        merge(proof['bindings'])
    events = proofs[-1]
    assert events['events'] == events['committed']+events['retained'] == 101534
    assert events['present_factor'] == 1 and all(events[k] is True for k in EVENT_FLAGS)
    assert proofs[1]['overflow_units'] == events['overflow_units'] == terminal['final_overflow']
    current, baseline = bind(model/'protocol.json'), bind(BASELINE/'model/protocol.json')
    assert 'targetLRU512;' in current['primary_search_policy']
    assert {k: v for k, v in current.items() if k not in ('bindings', 'primary_search_policy')} == {k: v for k, v in baseline.items() if k != 'bindings'}
    for name in ('initial.json', 'floors.json', 'round0.json', 'round1.json', 'sketch.json'):
        path = model/name
        bindings[str(path)] = sha(path)
        if name in ('initial.json', 'floors.json'):
            ref = BASELINE/'model'/name
            bindings[str(ref)] = sha(ref)
            assert bindings[str(path)] == bindings[str(ref)]
    receipt = model/'receipt.json'
    bindings[str(receipt)] = sha(receipt)
    counts, rounds = {}, []
    for kind, index, value in round_items(receipt):
        if kind == 'event':
            counts[index] = counts.get(index, 0)+1
        else:
            assert counts[index] == len(value['affected_nets']) == 50767
            rounds.append(index)
    assert rounds == [0, 1] and sum(counts.values()) == 101534
    cost = bind(model/'quotient_cache_cost.json')
    assert cost['cache_entries_limit'] == 512 and cost['lower_cache_evictions'] == 0
    assert cost['native_cache_entries'] <= 455 and cost['lower_cache_entries'] <= 455
    assert all(sha(path) == digest for path, digest in bindings.items())
    result = dict(all_pass=True, bindings=bindings, all_original_connections=77106,
        all_events=101534, all_three_independent_audits_pass=True, present_factor=1,
        scientific_protocol_unchanged_except_registered_search_and_cache=True,
        initial_and_floors_byte_identical=True, final_state_or_event_baseline_parity_assumed=False,
        stage_resources_and_terminals=resources, overflow_units=events['overflow_units'],
        complete_receipt_round_counts=counts, seconds=time.perf_counter()-started,
        quality_or_paired_performance_or_workflow_gain_proven=False, promoted=False,
        scope='Closed full-model software admission and complete receipt traversal. Independent original XML/Fraction audits supply physical/transaction evidence. No weighted-optimality recertification for every large query, future quality/nativeQoR/heldout/workflow/hardware claim.')
    with (OUT/'independent_final_admission_v1.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('PASS closed complete candidate admission', events['overflow_units'], flush=True)


if __name__ == '__main__':
    main()
