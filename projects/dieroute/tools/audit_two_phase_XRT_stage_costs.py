"""Recover measured disjoint stage durations; never infer a deadlock from timeout."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work/native_two_phase_identity_XRT_pipeline_20261015'

def main():
    refs = {}
    def read(name):
        p = SOURCE / name
        refs[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        return p.read_text()
    outcome = json.loads(read('independent_outcome_audit.json'))
    manifest = json.loads(read('manifest.json'))
    protocol = json.loads(read('protocol.json'))
    assert manifest['status'] == 'bounded_diagnostic_not_completed'
    assert protocol['maximum_probe_wall_seconds'] == 1800
    assert manifest['reason'] == 'predeclared_diagnostic_wall_bound'
    assert outcome['completed'] is False and outcome['wait_returns'] == []
    text = read('run.log')
    stages = [{'name': n, 'operation_or_index': int(a), 'value': int(b), 'steady_ns': int(t)}
              for n, a, b, t in re.findall(r'STAGE name=(\S+) a=(\d+) b=(\d+) steady_ns=(\d+)', text)]
    def one(name):
        values = [s for s in stages if s['name'] == name]
        assert len(values) == 1, name
        return values[0]
    setup_begin, setup_end, wait = [one(n) for n in ['commit_setup_begin', 'commit_setup_complete', 'kernel_wait_begin']]
    assert setup_begin['steady_ns'] < setup_end['steady_ns'] < wait['steady_ns']
    assert wait['operation_or_index'] == 3 and not any(s['name'] == 'kernel_wait_return' for s in stages)
    seeds = [int(x) for x in re.findall(r'DIAG seed_enqueue_wait_wall_ns=(\d+)', text)]
    searches = [int(x) for x in re.findall(r'DIAG snapshot_enqueue_wait_wall_ns=(\d+)', text)]
    assert len(seeds) == len(searches) == 1
    # Host source places seed wait, snapshot wait, and commit setup sequentially.
    host = read('source/tb/host.cpp')
    assert host.index('DIAG seed_enqueue_wait_wall_ns') < host.index('DIAG snapshot_enqueue_wait_wall_ns') < host.index('diagnostic_stage("commit_setup_begin")')
    setup = (setup_end['steady_ns'] - setup_begin['steady_ns']) / 1e9
    total = manifest['elapsed_wall_seconds']
    measured = sum(seeds + searches) / 1e9 + setup
    assert 0 < measured < total
    result = {'status': 'bounded_two_phase_XRT_disjoint_host_stage_costs_reviewed',
              'total_pipeline_wall_seconds': total, 'configured_pipeline_guard_seconds': 1800,
              'seed_enqueue_wait_seconds': sum(seeds) / 1e9,
              'snapshot_enqueue_wait_seconds': sum(searches) / 1e9,
              'commit_setup_seconds': setup,
              'unattributed_wall_seconds_upper_bound_for_proposal_wait': total - measured,
              'last_stage': wait, 'proposal_wait_completed': False,
              'source_sha256': refs,
              'scope': 'Existing bounded run only, no restart. Enqueue/wait durations include host/runtime and simulator work, not card execution time or pure CU cycle latency. Unattributed time includes earlier CPU checks, uploads, other setup and proposal wait; no exact proposal duration, kernel-start confirmation, deadlock diagnosis, throughput or energy claim. The 1800s cap applies to the entire pipeline, not a dedicated proposal wait.',
              'research_complete': False, 'board_result': False}
    result['source_sha256'][str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out = ROOT / 'work/two_phase_XRT_stage_costs_20261018'
    out.mkdir(exist_ok=False)
    (out / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['source_sha256', 'scope']}))

if __name__ == '__main__':
    main()
