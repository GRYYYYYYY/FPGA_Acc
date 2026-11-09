"""Compare actual online router artifacts against its frozen fresh-process reference."""
import argparse
import json
from pathlib import Path
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pair',type=Path);p.add_argument('online',type=Path)
    a=p.parse_args();pair=a.pair.resolve();online=a.online.resolve()
    reference=json.loads(pair.read_text());mode,=reference['modes']
    run=json.loads((online/'manifest.json').read_text())
    assert run['status']=='online_router_completed_equivalence_audit_required'
    prefix=mode+'_0';checks=[]
    for source in sorted(pair.parent.glob(prefix+'.*')):
        suffix=source.name[len(prefix):]
        if suffix.endswith('.log'):continue
        target=online/('route'+suffix)
        assert target.is_file(),target
        if suffix=='.json':
            expected=json.loads(source.read_text());actual=json.loads(target.read_text())
            expected.pop('wall_ms');actual.pop('wall_ms')
            assert actual==expected,suffix
            kind='all_json_fields_except_wall_ms'
        else:
            assert source.read_bytes()==target.read_bytes(),suffix
            kind='byte_equal'
        checks.append(dict(suffix=suffix,comparison=kind,reference_sha256=sha(source),online_sha256=sha(target)))
    epochs=reference['modes'][mode]['runs'][0]['iterations']
    assert run['requests']==epochs
    assert sum(c['suffix'].endswith('.input.csv') for c in checks)==epochs
    assert sum(c['suffix'].endswith('.output.csv') for c in checks)==epochs
    report=dict(status='online_router_all_reference_artifacts_equivalent_except_wall_ms',checks=checks,epochs=epochs,source_sha256={str(p):sha(p) for p in [pair,online/'manifest.json',Path(__file__).resolve()]},scope='Exact observed online route/state/timing equivalence to frozen reference;not paired runtime evidence,universal equivalence or board evaluation',board_result=False,research_complete=False)
    (online/'equivalence_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],artifacts=len(checks),epochs=epochs)))
