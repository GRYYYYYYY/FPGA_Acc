"""Execute the frozen eight-candidate local sketch shell before native labels."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    start = time.perf_counter()
    cohort = R / 'experiments/xtea_placement_feedback_cohort_v2_2026-10-13'
    out = R / 'experiments/xtea_placement_feedback_decisions_v1_2026-10-13'
    out.mkdir()
    cp = cohort / 'verification.json'
    certified = json.loads(cp.read_text())
    assert certified['all_eight_legal_moves_and_complete_endpoint_identity_pass']
    assert not certified['native_route_labels_generated']
    protocol = json.loads((cohort / 'protocol.json').read_text())
    scripts = [R / 'tools' / s for s in ['prepare_fixed_epoch_placement_candidate_v1.py', 'run_warm_epoch_retained_update_v1.py', 'verify_resident_demand_frame_direct_lattice_v7.py', 'verify_warm_epoch_retained_update_v1.py']]
    bindings = {**closure([Path(__file__), *scripts]), **certified['bindings'], str(cp): sha(cp)}
    original = R / 'experiments/xtea_design_scoped_retained_pipeline_v1_2026-10-13/model'
    baseline = json.loads((original / 'sketch.json').read_text())
    for name in ['initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json']:
        p = original / name
        v = json.loads(p.read_text())
        assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
        assert all(sha(q) == h for q, h in v['bindings'].items())
        bindings.update(v['bindings'])
        bindings[str(p)] = sha(p)
    bindings[str(original / 'sketch.json')] = sha(original / 'sketch.json')
    rows = [dict(candidate_id=0, hpwl=protocol['baseline_hpwl'], sketch_overflow=baseline['overflow_units'], endpoint=protocol['baseline_endpoint'])]
    frozen = dict(bindings=bindings, cohort_protocol=str(cohort / 'protocol.json'), placement_shell=protocol['placement_shell'], order=[r['candidate_id'] for r in certified['rows']], baseline_sketch_overflow=baseline['overflow_units'], scope='Exposed-design frozen placement shell; isolated candidate models, fixed timing epoch. All native outcomes generated only after decision freeze. This driver includes model preparation and correctness audits; it is not a matched on/off full workflow timer.')
    assert all(sha(p) == h for p, h in bindings.items())
    (out / 'protocol.json').write_text(json.dumps(frozen, indent=2) + '\n')
    env = {k: v for k, v in os.environ.items() if not k.startswith('ROUTECAST_')}
    for item in certified['rows']:
        cid = item['candidate_id']
        directory = out / ('candidate_%02d' % cid)
        directory.mkdir()
        prep, model = directory / 'prepared', directory / 'model'
        commands = [
            ('prepare', [str(scripts[0]), str(cohort), str(cid), str(prep)]),
            ('model', [str(scripts[1]), item['endpoint'], str(model), str(prep / 'base/verification.json'), str(prep / 'timing'), str(prep / 'warm'), 'local']),
            ('initial_audit', [str(scripts[2]), str(model), 'initial', str(model / 'initial_physical_verification.json')]),
            ('sketch_audit', [str(scripts[2]), str(model), 'sketch', str(model / 'sketch_physical_verification.json')]),
            ('event_audit', [str(scripts[3]), str(model), 'xtea', str(model / 'verification.json')]),
        ]
        times = {}
        for stage, args in commands:
            print('PLACEMENT START', cid, stage, flush=True)
            tick = time.perf_counter()
            with (directory / (stage + '.log')).open('x') as log:
                status = subprocess.call([sys.executable, *args], cwd=R, env=env, stdout=log, stderr=subprocess.STDOUT)
            times[stage] = time.perf_counter() - tick
            (directory / (stage + '_terminal.json')).write_text(json.dumps(dict(exit_status=status, process_seconds=times[stage])) + '\n')
            if status:
                raise SystemExit(status)
        for name in ['initial_physical_verification.json', 'sketch_physical_verification.json', 'verification.json']:
            v = json.loads((model / name).read_text())
            assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
        sketch = json.loads((model / 'sketch.json').read_text())
        receipt = json.loads((model / 'receipt.json').read_text())
        warm = json.loads((prep / 'warm/verification.json').read_text())
        rows.append(dict(candidate_id=cid, hpwl=item['hpwl'], sketch_overflow=sketch['overflow_units'], endpoint=item['endpoint'], model=str(model), staged_dirty_nets=len(warm['dirty_nets']), primary_search_calls=sum(e['primary_search_calls'] for r in receipt['rounds'] for e in r['events']), stage_seconds=times, all_physical_and_event_checks_pass=True))
        (out / 'rows.json').write_text(json.dumps(rows, indent=2) + '\n')
        (directory / 'pipeline_terminal.json').write_text(json.dumps(dict(all_stages_completed=True, exit_status=0)) + '\n')
        print('PLACEMENT PASS', cid, 'HPWL', item['hpwl'], 'overflow', sketch['overflow_units'], flush=True)
    baseline_overflow = rows[0]['sketch_overflow']
    admitted = [r for r in rows if r['sketch_overflow'] <= baseline_overflow]
    key = lambda r: (r['hpwl'], r['candidate_id'])
    off = min(rows, key=key)
    on = min(admitted, key=key)
    assert not list(out.rglob('*.route'))
    assert all(sha(p) == h for p, h in bindings.items())
    decision = dict(cohort_protocol_sha256=sha(cohort / 'protocol.json'), rows=rows, off_candidate=off['candidate_id'], on_candidate=on['candidate_id'], on_admitted_candidates=[r['candidate_id'] for r in admitted], native_labels_generated=False, baseline_retained_until_symmetric_native_gate=True, full_decision_driver_seconds=time.perf_counter() - start)
    (out / 'decision.json').write_text(json.dumps(decision, indent=2) + '\n')
    for p in out.rglob('*'):
        if p.is_file():
            bindings[str(p)] = sha(p)
    (out / 'verification.json').write_text(json.dumps(dict(bindings=bindings, all_eight_candidate_models_and_physical_event_audits_pass=True, decisions_frozen_before_new_native_labels=True, decision_sha256=sha(out / 'decision.json'), off_candidate=off['candidate_id'], on_candidate=on['candidate_id'], native_acceptance_pending=True, scope=frozen['scope']), indent=2) + '\n')
    print('DECISIONS FROZEN', off['candidate_id'], on['candidate_id'], flush=True)


if __name__ == '__main__':
    main()
