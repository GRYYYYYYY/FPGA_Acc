"""Check that attachment tracing preserves all original routing observables."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('traced',type=Path);p.add_argument('original',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths=[a.traced.resolve(),a.original.resolve()]
    checked=[audit(path) for path in paths];new,old=[json.loads(path.read_text()) for path in paths]
    for key in ('configuration','case','reference','native_run_sha256','reference_sha256','timing_vpr','native_cost_export'):
        assert new[key]==old[key],key
    assert new['source_sha256'].keys()==old['source_sha256'].keys()
    changed={k for k,v in new['source_sha256'].items() if v!=old['source_sha256'][k]}
    assert changed=={'source/dieroute/include/wide_costs.hpp','source/dieroute/src/wide_controller.cpp',
                     'source/dieroute/host/rr_host.cpp','source/dieroute/tools/run_rr_pair.py'}
    for suffix in ('nodes','edges','resources','tasks'):
        assert (paths[0].parent/('input.'+suffix)).read_bytes()==(paths[1].parent/('input.'+suffix)).read_bytes()
    assert new['modes'].keys()==old['modes'].keys();count=0
    for mode in old['modes']:
        for i in range(5):
            previous=old['modes'][mode]['hashes'][i];current=new['modes'][mode]['hashes'][i]
            assert set(current)==set(previous)|{'attachments.csv','attachment_branches.csv'}
            assert all(current[k]==v for k,v in previous.items());count+=len(previous)
            before=old['modes'][mode]['runs'][i];after=new['modes'][mode]['runs'][i]
            assert {k:v for k,v in after.items() if k!='wall_ms'}=={k:v for k,v in before.items() if k!='wall_ms'}
        assert checked[0]['modes'][mode]['native_qor']==checked[1]['modes'][mode]['native_qor']
    files=paths+[Path(__file__),Path(__file__).with_name('audit_rr_experiments.py')]
    report=dict(status='five_repeat_attachment_trace_compatibility_audited',equal_common_artifacts=count,
                changed_sources=sorted(changed),source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                scope='Declared four-file tracing extension; original inputs/config and five-repeat common output hashes/counters/native QoR identical. Compatibility only, no runtime or mechanism improvement claim.',
                research_complete=False,board_result=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],equal_common_artifacts=count)))
