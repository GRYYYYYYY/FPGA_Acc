"""Separate recorded CPU prototype costs; never infer accelerator speedup."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    output = Path(sys.argv[1]).resolve()
    refs = {}

    def read(name):
        path = root / name
        refs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    baseline = read('work/prospective_apex2_seeds6_10_baselines_20261020/independent_audit.json')
    base, = [v for v in baseline['outcomes'] if v['seed'] == 6]
    parent = read('work/prospective_apex2_seeds6_10_parents_v2_20261020/parents/apex2_seed6/route.json')
    search_events = []
    for folder in [
        'work/posterior_critical_minimum_blocker_exchange_20261020/apex2_seed6_task243',
        'work/posterior_critical_minimum_blocker_exchange_20261020/apex2_seed6_task3481',
        'work/posterior_seed6_exchange_followup_20261020/task2005',
        'work/posterior_seed6_exchange_followup_20261020/task588',
    ]:
        generation = read(folder + '/manifest.json')
        assert generation['status'] == 'budgeted_exchange_arms_terminal_require_review'
        search_events.extend({'generation': folder, 'arm': v['name'], 'status': v['status'],
                              'wall_ns': v['wall_ns']} for v in generation['arms'])
    assert len(search_events) == 6
    native_events = []
    for folder in [
        'work/posterior_critical_minimum_blocker_exchange_20261020/apex2_seed6_task243',
        'work/posterior_seed6_exchange_followup_20261020/task2005',
        'work/posterior_seed6_exchange_followup_20261020/task588',
    ]:
        audit = read(folder + '/native_queue/target_first_order0/independent_native_audit.json')
        native_events.append({'generation': folder, 'wall_ns': audit['validation_wall_ns'],
                              'joint_pass': all(audit['checks'].values())})
    cleanup = read('work/posterior_seed6_bounded_wire_cleanup_20261020/apex2_seed6/manifest.json')
    assert cleanup['termination_reason'] == 'joint_baseline_met'
    cleanup_ns = sum(v['wall_ns'] for v in cleanup['steps'])
    observation_events = []
    for category, folder in [
        ('diagnosis', 'work/prospective_parent_critical_delay_diagnosis_20261020/apex2_seed6'),
        ('followup_refresh', 'work/posterior_seed6_exchange_followup_20261020'),
        ('final_verification', 'work/posterior_seed6_final_joint_pass_native_recheck_20261020'),
    ]:
        manifest = read(folder + '/manifest.json')
        assert manifest['status'] == 'all_native_RC_observations_terminal_requires_review'
        observation_events.extend({'category': category, 'case': v['name'], 'wall_ns': v['wall_ns']}
                                  for v in manifest['cases'])
    # These fields are disjoint measured intervals, but omit other work and
    # cannot be interpreted as total elapsed wall time of an overlapping study.
    partial_ns = sum(v['wall_ns'] for v in search_events + native_events + observation_events) + cleanup_ns
    refs[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report = {'status': 'seed6_posterior_recorded_cpu_cost_components_reviewed',
              'baseline_generation_seconds': base['elapsed_ns'] / 1e9,
              'cpp_parent_reported_seconds': parent['wall_ms'] / 1000,
              'private_exchange_searches': search_events, 'exchange_native_validation': native_events,
              'cleanup_trial_seconds_including_search_and_native_validation': cleanup_ns / 1e9,
              'native_observation_intervals': observation_events,
              'recorded_postprocessing_component_sum_seconds': partial_ns / 1e9,
              'source_sha256': refs, 'research_complete': False, 'board_result': False,
              'scope': 'Six seed6 search arms, three unique exchange native checks, one cleanup trial, diagnosis/refresh/final verification intervals. Component sum excludes cleanup initial reload, graph preparation, lower-bound probes, audits, orchestration and unrecorded exploratory work. Parent C++ timer and baseline generation timer have different scopes; no matched timing ratio, complete end-to-end cost, FPGA speedup or energy claim.'}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: report[k] for k in ['baseline_generation_seconds', 'cpp_parent_reported_seconds',
                                            'recorded_postprocessing_component_sum_seconds']}))


if __name__ == '__main__':
    main()
