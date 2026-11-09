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
    p.add_argument('--semantic-audits',type=Path,nargs=3,required=True)
    p.add_argument('--version-audits',type=Path,nargs=3,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths=[a.control.resolve(),a.candidate.resolve(),a.guarded.resolve()]
    verified=[audit(path) for path in paths];manifests=[json.loads(path.read_text()) for path in paths]
    keys={'supplemental_transaction_mode'}
    assert [m['configuration']['supplemental_transaction_mode'] for m in manifests]==[0,1,2]
    assert all(m['configuration']['criticality_feedback_threshold_q']==64880 and m['configuration']['feedback_local_delay_guard'] is True for m in manifests)
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
                assert env.pop('DIEROUTE_SUPPLEMENTAL_TRANSACTION_MODE')==str(m['configuration']['supplemental_transaction_mode'])
                interpreter,adapter=shlex.split(env['PERSISTROUTE_TIMING_COMMAND'])
                env['PERSISTROUTE_TIMING_COMMAND']=[interpreter,hashlib.sha256(Path(adapter).read_bytes()).hexdigest()]
                environments.append(env)
            assert all(env==environments[0] for env in environments)
    semantic_paths=[p.resolve() for p in a.semantic_audits]
    version_paths=[p.resolve() for p in a.version_audits]
    for index,pair in enumerate(paths):
        for proof_path,status in [(semantic_paths[index],'five_repeat_net_trial_paths_pending_and_predicates_audited'),
                                  (version_paths[index],'private_and_published_versions_match_trial_epoch_and_final_checkpoints')]:
            proof=json.loads(proof_path.read_text());assert proof['status']==status
            assert proof['source_sha256'][str(pair)]==hashlib.sha256(pair.read_bytes()).hexdigest()
            assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in proof['source_sha256'].items())
            assert proof['modes'].keys()==verified[index]['modes'].keys()
    sources=paths+semantic_paths+version_paths+[Path(__file__),Path(__file__).with_name('audit_rr_experiments.py')]
    report=dict(status='same_source_supplemental_net_trial_three_arms_audited',
                outcomes={label:v['modes'] for label,v in zip(('parent','staged','guarded'),verified)},
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
                scope='One development-case three-arm comparison with full sources, inputs, config and environments matched except supplemental transaction mode. Requires passed complete path/pending/predicate and private/published version replay for each arm. Outcomes may fail quality/convergence; no general, novelty or board claim.',
                research_complete=False,board_result=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'])))
