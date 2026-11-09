"""Audit all ten native adaptive-placement runs and retain the joint quality gate."""
import argparse,hashlib,json
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('study',type=Path);a=p.parse_args();root=a.study.resolve()
    output=root/'independent_audit.json';assert not output.exists()
    files=[Path(__file__).resolve()]
    def read(path):files.append(path);return json.loads(path.read_text())
    def verify(proof):
        assert proof['source_sha256']
        for name,value in proof['source_sha256'].items():assert sha(name)==value,name
    result=read(root/'native_result.json');verify(result)
    assert result['status']=='ten_native_static_adaptive_migration_runs_and_independent_audits_complete'
    manifest=read(root/'native_manifest.json');assert manifest['status']==result['status']
    assert len(manifest['steps'])==34 and all(s['status']=='passed' and s['returncode']==0 for s in manifest['steps'])
    outcomes={}
    for arm in ['static','adaptive']:
        last=None;stats=[]
        for repeat in range(5):
            directory=root/'native_runs'/f'{arm}_{repeat}'
            state=read(directory/'resource_replay_audit.json');verify(state)
            assert state['cpu_legal'] and state['final_resources_and_costs_byte_equivalent']
            credit=read(directory/'credit_replay_audit.json');verify(credit)
            assert credit['final_credits_empty'] and credit['tickets']==state['received_task_requests_checked']
            if arm=='adaptive':assert credit['decision_requests_checked']==state['adaptive_decisions_checked']==credit['tickets']
            for name in ['tree_audit.json','session_provenance_audit.json']:
                proof=read(directory/name);verify(proof)
            compare=read(directory/'static_parent_compatibility.json')
            assert compare['checks']
            for row in compare['checks']:
                assert sha(directory/('route'+row['suffix']))==row['candidate_sha256']
            report=read(directory/'route.json');report.pop('wall_ms')
            hashes={path.name:sha(path) for path in directory.glob('route.*') if path.name!='route.json'}
            if last is not None:assert last==(report,hashes)
            last=(report,hashes)
            stats.append(dict(transfers=credit['tickets'],backpressure=credit['events'].get('backpressure',0),remote_read_entries=report['remote_shadow_reads'],received_seed_rows=state['received_seed_rows_checked'],checked_policy_windows=state.get('adaptive_windows_checked',0)))
        assert all(row==stats[0] for row in stats)
        native=result['outcomes'][arm]['native_qor']
        checks=dict(native_legal=native['legal'],wirelength_nondegrade=native['total_wirelength']<=native['baseline_wirelength'],cpd_nondegrade=native['critical_path_delay_ns']<=native['baseline_cpd_ns'])
        outcomes[arm]=dict(repeats=5,per_repeat=stats[0],native_qor={k:native[k] for k in ['total_wirelength','critical_path_delay_ns','baseline_wirelength','baseline_cpd_ns','wirelength_delta_percent','cpd_delta_percent']},checks=checks,joint_quality_pass=all(checks.values()))
    assert outcomes['static']['native_qor']==outcomes['adaptive']['native_qor']
    x,y=[outcomes[arm]['per_repeat'] for arm in ['static','adaptive']]
    report=dict(status='ten_native_adaptive_migration_runs_independently_audited_quality_gate_still_failed',outcomes=outcomes,
        backpressure_event_change_percent=100*(y['backpressure']/x['backpressure']-1),
        remote_read_entry_change_percent=100*(y['remote_read_entries']/x['remote_read_entries']-1),
        source_sha256={str(f):sha(f) for f in files},
        scope='Same frozenReleasebinary,staticdestination/adaptive3,entrycredit1,sync1,5ex5prepeats perarm. Fullauthoritativepressure/score/credit/seed/resource/version/tree/provenance/nativechecks. Adaptive changes backpressure/remoteclassifiedjournal counts withidenticalnativeQoR,stillfailingstrongbaseline. Countsarenotmeasurednetworkbytes,latency,physicalperformance orpolicyoptimality;independentfullsearchaccessenumeration andhardware remainopen.',
        adopted=False,board_result=False,research_complete=False)
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','scope','outcomes']}))


if __name__=='__main__':main()
