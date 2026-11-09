"""Match full sources and executed settings for three feedback-arm outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
from audit_rr_experiments import audit

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('control',type=Path);p.add_argument('candidate',type=Path)
    p.add_argument('guarded',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths=[a.control.resolve(),a.candidate.resolve(),a.guarded.resolve()]
    verified=[audit(path) for path in paths];manifests=[json.loads(path.read_text()) for path in paths]
    keys={'criticality_feedback_threshold_q','feedback_local_delay_guard'}
    assert [(m['configuration']['criticality_feedback_threshold_q'],m['configuration']['feedback_local_delay_guard']) for m in manifests]==[(0,False),(64880,False),(64880,True)]
    x=manifests[0]
    for y in manifests[1:]:
        assert {k:v for k,v in x['configuration'].items() if k not in keys}=={k:v for k,v in y['configuration'].items() if k not in keys}
        for field in ('case','reference','native_run_sha256','reference_sha256','native_cost_export','timing_vpr','source_sha256'):
            assert x[field]==y[field],field
        assert x['modes'].keys()==y['modes'].keys()
    for suffix in ('nodes','edges','resources','tasks'):
        assert len({hashlib.sha256((path.parent/('input.'+suffix)).read_bytes()).hexdigest() for path in paths})==1
    for mode in x['modes']:
        for i in range(5):
            environments=[]
            for m in manifests:
                step,=[s for s in m['steps'] if s['label']==f'{mode}_{i}'];env=dict(step['routing_environment'])
                assert env.pop('DIEROUTE_CRITICAL_FEEDBACK_THRESHOLD_Q')==str(m['configuration']['criticality_feedback_threshold_q'])
                assert env.pop('DIEROUTE_FEEDBACK_LOCAL_DELAY_GUARD')==str(int(m['configuration']['feedback_local_delay_guard']))
                interpreter,adapter=shlex.split(env['PERSISTROUTE_TIMING_COMMAND'])
                env['PERSISTROUTE_TIMING_COMMAND']=[interpreter,hashlib.sha256(Path(adapter).read_bytes()).hexdigest()]
                environments.append(env)
            assert all(env==environments[0] for env in environments)
    sources=paths+[Path(__file__),Path(__file__).with_name('audit_rr_experiments.py')]
    report=dict(status='same_source_local_delay_feedback_three_arms_audited',
                outcomes={label:v['modes'] for label,v in zip(('disabled','unguarded','guarded'),verified)},
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
                scope='One development-case three-arm comparison with full sources, inputs, config and environments matched except threshold and local-delay guard. Outcomes may fail quality/convergence; no general, novelty or board claim.',
                research_complete=False,board_result=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'])))
