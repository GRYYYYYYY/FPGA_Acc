"""Pure readiness boundaries; stage execution uses the already-tested v2 guard."""
from pathlib import Path
import run_neuron_no_retention_postprocess_v1 as queue


def main():
    live=dict(verified_identity=True,verified_live=True,state='S',command_matches=True)
    gone=dict(status='missing_not_terminal_evidence',verified_live=False)
    good=dict(exit_status=0,all_stages_completed=True)
    cases=[(None,live,'waiting'),(None,gone,'unresolved'),(good,live,'waiting'),(good,gone,'ready'),
        (dict(exit_status=1,all_stages_completed=True),gone,'failed'),
        (dict(exit_status=False,all_stages_completed=True),gone,'failed'),
        (dict(exit_status=0,all_stages_completed=False),gone,'unresolved'),
        (good,dict(verified_identity=False),'ready'),(good,dict(state='Z'),'ready'),
        (None,{},'waiting')]
    for terminal,observed,expected in cases:
        assert queue.readiness(terminal,observed)==expected
    assert queue.trial.run_stage is __import__('neuron_no_retention_trial_v2').run_stage
    r=queue.trial.R/'experiments/no_retention_postprocess_guard_v1_2026-10-17';r.mkdir()
    queue.trial.write(r/'verification.json',dict(all_pass=True,readiness_boundaries=len(cases),
        uses_already_validated_v2_real_child_resource_timeout_no_retry_function=True,
        no_job_submitted=True,bindings={str(p.resolve()):queue.trial.sha(p) for p in (Path(__file__),Path(queue.__file__),Path(queue.trial.__file__))}))
    print('PASS',len(cases),'readiness boundaries; no jobs launched')


if __name__ == '__main__':
    main()
