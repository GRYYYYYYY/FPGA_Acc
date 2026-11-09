"""Check the bulk-wave controller against its corresponding feedback parent."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('extended',type=Path);p.add_argument('parent',type=Path)
    p.add_argument('--state-audit',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths=[a.extended.resolve(),a.parent.resolve()];checked=[audit(path) for path in paths]
    new,old=[json.loads(path.read_text()) for path in paths]
    assert new['configuration']['ordinary_schedule_mode']==0
    assert new['configuration']['supplemental_transaction_mode']==0
    assert {k:v for k,v in new['configuration'].items() if k not in ('supplemental_transaction_mode','ordinary_schedule_mode')}==old['configuration']
    for key in ('case','reference','native_run_sha256','reference_sha256','native_cost_export','timing_vpr'):
        assert new[key]==old[key],key
    assert new['source_sha256'].keys()==old['source_sha256'].keys()
    changed={k for k,v in new['source_sha256'].items() if old['source_sha256'][k]!=v}
    assert changed=={'source/dieroute/include/wide_costs.hpp','source/dieroute/src/wide_controller.cpp',
                     'source/dieroute/host/rr_host.cpp','source/dieroute/tools/run_rr_pair.py'}
    assert new['modes'].keys()==old['modes'].keys();count=0
    for suffix in ('nodes','edges','resources','tasks'):
        assert (paths[0].parent/('input.'+suffix)).read_bytes()==(paths[1].parent/('input.'+suffix)).read_bytes()
    for mode in old['modes']:
        for i in range(5):
            before=old['modes'][mode]['hashes'][i];after=new['modes'][mode]['hashes'][i]
            assert set(after)==set(before)|{'net_trials.csv','net_trial_steps.csv','net_trial_seeds.csv','net_trial_branches.csv','net_trial_connections.csv','net_trial_paths.csv','ordinary_ripups.csv'}
            import csv
            for suffix in set(after)-set(before):
                with (paths[0].parent/f'{mode}_{i}.{suffix}').open() as stream:
                    reader=csv.DictReader(stream);assert reader.fieldnames
                    rows=list(reader)
                    if suffix!='ordinary_ripups.csv':assert not rows, 'No private trials in this study'
                    else:
                        assert len(rows)==new['modes'][mode]['runs'][i]['ordinary_ripup_events']
                        assert all(int(r['phase'])==0 and int(r['dispatch_batch'])==0 and int(r['iteration'])>0 for r in rows)
            assert all(after[k]==v for k,v in before.items());count+=len(before)
            previous=old['modes'][mode]['runs'][i];current=new['modes'][mode]['runs'][i]
            assert {k:v for k,v in current.items() if k not in ('wall_ms','supplemental_transaction_mode','net_trial_count','ordinary_schedule_mode','ordinary_ripup_events')}=={k:v for k,v in previous.items() if k!='wall_ms'}
        assert checked[0]['modes'][mode]['native_qor']==checked[1]['modes'][mode]['native_qor']
    proof_path=a.state_audit.resolve();proof=json.loads(proof_path.read_text())
    assert proof['status']=='five_repeat_ordinary_schedule_paths_ripups_and_versions_audited'
    assert proof['source_sha256'][str(paths[0])]==hashlib.sha256(paths[0].read_bytes()).hexdigest()
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in proof['source_sha256'].items())
    sources=paths+[proof_path,Path(__file__),Path(__file__).with_name('audit_rr_experiments.py')]
    report=dict(status='five_repeat_bulk_schedule_parent_compatibility_audited',
                equal_common_artifacts=count,changed_sources=sorted(changed),
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
                scope='Declared bulk-mode four-file extension with six empty private sidecars and separately replayed bulk ripup log; five-repeat common artifacts/counters/native QoR identical. Compatibility, not timing/runtime improvement or new hardware evidence.',
                research_complete=False,board_result=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],equal_common_artifacts=count)))
