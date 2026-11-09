"""Compare audited local/preserve task orders with otherwise matched execution."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit
from compare_rr_cost_precision import match_settings

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('local',type=Path)
    parser.add_argument('preserve',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    paths = (args.local.resolve(),args.preserve.resolve())
    results = [audit(p) for p in paths]
    manifests = [json.loads(p.read_text()) for p in paths]
    matched = match_settings(*manifests,varying='task_order',expected=('local_distance','preserve'))
    assert manifests[0]['source_sha256'] == manifests[1]['source_sha256'], 'Source/runner contents differ'
    for suffix in ('nodes','edges','resources','tasks'):
        data = [(p.parent/('input.'+suffix)).read_bytes() for p in paths]
        assert data[0] == data[1],suffix
    outcomes = {name: result['modes'] for name,result in zip(('local_distance','preserve'),results)}
    report = dict(status='same_source_task_order_pair_audited',matched_core_files=matched,
                  outcomes=outcomes,scope='Matched one-case development comparison; no general QoR or board claim',
                  manifests_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  board_result=False,research_complete=False)
    assert not args.output.exists(), 'Preserve existing comparisons'
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],matched_core_files=matched)))
