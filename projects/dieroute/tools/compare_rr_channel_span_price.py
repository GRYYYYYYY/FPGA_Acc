"""Audit the surcharge/control channel span price development pair."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit
from compare_rr_cost_precision import match_settings

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('priced',type=Path);p.add_argument('control',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    paths=[a.priced.resolve(),a.control.resolve()]
    verified=[audit(path) for path in paths]
    manifests=[json.loads(path.read_text()) for path in paths]
    matched=match_settings(*manifests,varying='channel_span_price_q',expected=(64,0))
    assert manifests[0]['source_sha256']==manifests[1]['source_sha256']
    for suffix in ('nodes','edges','resources','tasks'):
        assert (paths[0].parent/('input.'+suffix)).read_bytes()==(paths[1].parent/('input.'+suffix)).read_bytes()
    report=dict(status='same_source_channel_span_price_pair_audited',matched_core_files=matched,
                outcomes={name:v['modes'] for name,v in zip(('priced','control'),verified)},
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
                               paths+[Path(__file__),Path(__file__).with_name('compare_rr_cost_precision.py'),Path(__file__).with_name('audit_rr_experiments.py')]},
                scope='One CPU development case; matched full sources/input/config/environment except channel span surcharge. Neither general quality acceptance nor board performance.',
                research_complete=False,board_result=False)
    assert not a.output.exists()
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],matched_core_files=matched)))
