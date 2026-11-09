"""Matched-source cleanup comparison including preserved pre-cleanup history."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit
from compare_rr_cost_precision import match_settings

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('enabled',type=Path)
    parser.add_argument('disabled',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    paths = (args.enabled.resolve(),args.disabled.resolve())
    results = [audit(p) for p in paths]
    manifests = [json.loads(p.read_text()) for p in paths]
    matched = match_settings(*manifests,varying='cleanup_passes',expected=(2,0))
    assert manifests[0]['source_sha256'] == manifests[1]['source_sha256']
    for suffix in ('nodes','edges','resources','tasks'):
        assert (paths[0].parent/('input.'+suffix)).read_bytes() == (paths[1].parent/('input.'+suffix)).read_bytes()
    for mode in manifests[0]['modes']:
        for repeat in range(5):
            prefixes = [p.parent/f'{mode}_{repeat}' for p in paths]
            for suffix in ('costs','iterations.csv','timing_iterations.csv'):
                assert Path(str(prefixes[0])+'.'+suffix).read_bytes() == Path(str(prefixes[1])+'.'+suffix).read_bytes(),suffix
            if manifests[0]['modes'][mode]['runs'][repeat]['legal']:
                before = Path(str(prefixes[0])+'.audit.csv').read_text().splitlines()
                control = Path(str(prefixes[1])+'.audit.csv').read_text().splitlines()
                assert before[:-1] == control, 'Pre-cleanup controller history changed'
        enabled = results[0]['modes'][mode]['counters']
        disabled = results[1]['modes'][mode]
        if disabled.get('native_qor'):
            assert enabled['cleanup_wirelength_before'] == disabled['native_qor']['total_wirelength']
    report = dict(status='same_source_cleanup_pair_audited',matched_core_files=matched,
                  outcomes={name:r['modes'] for name,r in zip(('cleanup','disabled'),results)},
                  scope='One CPU development case, matched code/config and unchanged negotiation history; no general QoR or device rollback claim',
                  manifests_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  research_complete=False,board_result=False)
    assert not args.output.exists(), 'Preserve prior comparisons'
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],matched_core_files=matched)))
