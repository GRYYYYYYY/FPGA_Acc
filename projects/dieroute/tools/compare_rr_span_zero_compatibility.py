"""Verify disabling the span-price extension reproduces its parent controller."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extended',type=Path);p.add_argument('parent',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths=[a.extended.resolve(),a.parent.resolve()]
    checked=[audit(path) for path in paths];new,old=[json.loads(path.read_text()) for path in paths]
    assert new['configuration']['channel_span_price_q']==0
    assert {k:v for k,v in new['configuration'].items() if k!='channel_span_price_q'}==old['configuration']
    for field in ('case','reference','native_run_sha256','reference_sha256','native_cost_export','timing_vpr'):
        assert new[field]==old[field],field
    added=set(new['source_sha256'])-set(old['source_sha256'])
    removed=set(old['source_sha256'])-set(new['source_sha256'])
    changed={k for k in old['source_sha256'] if new['source_sha256'].get(k)!=old['source_sha256'][k]}
    assert not removed and added=={'source/dieroute/include/channel_span_cost.hpp'}
    assert changed=={'source/dieroute/host/rr_host.cpp','source/dieroute/tools/run_rr_pair.py'}
    for suffix in ('nodes','edges','resources','tasks'):
        assert (paths[0].parent/('input.'+suffix)).read_bytes()==(paths[1].parent/('input.'+suffix)).read_bytes()
    equal_artifacts=0
    for mode,entry in old['modes'].items():
        assert new['modes'].keys()==old['modes'].keys()
        for repeat in range(5):
            before=entry['hashes'][repeat];after=new['modes'][mode]['hashes'][repeat]
            assert set(after)==set(before)|{'effective.edges'}
            assert all(after[k]==v for k,v in before.items())
            equal_artifacts+=len(before)
            previous=entry['runs'][repeat];current=new['modes'][mode]['runs'][repeat]
            assert {k:v for k,v in current.items() if k not in ('wall_ms','channel_span_price_q')}=={k:v for k,v in previous.items() if k!='wall_ms'}
        assert checked[0]['modes'][mode]['native_qor']==checked[1]['modes'][mode]['native_qor']
    files=paths+[Path(__file__),Path(__file__).with_name('audit_rr_experiments.py')]
    report=dict(status='five_repeat_disabled_span_extension_compatibility_audited',
                equal_common_artifacts=equal_artifacts,changed_sources=sorted(changed),added_sources=sorted(added),
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                scope='Two different source versions: exact declared source delta, same inputs/config, all common routing outputs/counters and native QoR equal at span price0. Compatibility evidence only; not a same-source causal comparison or runtime result.',
                board_result=False,research_complete=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],equal_common_artifacts=equal_artifacts)))
