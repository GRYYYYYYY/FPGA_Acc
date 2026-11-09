"""Verify actual kernel RLIMIT and escalation on a resistant own child only."""
import hashlib
import json
from pathlib import Path
import neuron_no_retention_trial_v2 as trial


def main():
    out = trial.R/'experiments/no_retention_v2_kernel_limit_and_kill_v1_2026-10-17'
    out.mkdir()
    limit = 64*2**20
    code = "import resource,signal,time,json; signal.signal(signal.SIGTERM,signal.SIG_IGN); print(json.dumps({'rlimit':resource.getrlimit(resource.RLIMIT_AS)}),flush=True); time.sleep(90)"
    try:
        trial.run_stage(out, 'resistant_child', ['-c', code], limit, 1)
    except AssertionError as error:
        assert 'Failed/timed-out' in str(error)
    else:
        raise AssertionError('Resistant child unexpectedly succeeded')
    terminal = trial.load(out/'resistant_child_terminal.json')
    actual = json.loads((out/'resistant_child.log').read_text())
    assert actual['rlimit'] == [limit, limit]
    assert terminal['timed_out'] is True and terminal['exit_status'] == -9
    assert trial.gone(out, 'resistant_child_process.json')
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
    try:
        trial.run_stage(out, 'resistant_child', ['-c', 'raise SystemExit(0)'], limit, 1)
    except AssertionError as error:
        assert 'no retry' in str(error)
    else:
        raise AssertionError('Failed stage retried')
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
    proof = dict(all_pass=True, actual_kernel_soft_and_hard_limit_bytes=actual['rlimit'],
        resistant_own_child_terminated_by_SIGKILL=True, timeout_terminal=terminal,
        retry_refused_without_mutation=True, no_scientific_job_submitted=True,
        bindings={str(p.resolve()):trial.sha(p) for p in (Path(__file__),Path(trial.__file__))})
    trial.write(out/'verification.json', proof)
    print(json.dumps(proof,indent=2))


if __name__ == '__main__':
    main()
