"""Require exact default-preset compatibility with the frozen ordinary bulk parent."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_present_experiments import audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('extended', type=Path)
    parser.add_argument('parent', type=Path)
    parser.add_argument('--state-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = [args.extended.resolve(), args.parent.resolve()]
    checked = [audit(p) for p in paths]
    new, old = [json.loads(p.read_text()) for p in paths]
    assert new['configuration']['present_schedule_mode'] == 0
    assert {k:v for k,v in new['configuration'].items() if k != 'present_schedule_mode'} == old['configuration']
    for key in ('case','reference','native_run_sha256','reference_sha256','native_cost_export','timing_vpr'):
        assert new[key] == old[key], key
    assert new['source_sha256'].keys() == old['source_sha256'].keys()
    changed = {k for k,v in new['source_sha256'].items() if v != old['source_sha256'][k]}
    assert changed == {'source/dieroute/include/wide_costs.hpp', 'source/dieroute/src/wide_costs.cpp',
                       'source/dieroute/src/wide_controller.cpp', 'source/dieroute/host/rr_host.cpp',
                       'source/dieroute/tools/run_rr_pair.py'}
    for suffix in ('nodes','edges','resources','tasks'):
        assert (paths[0].parent/f'input.{suffix}').read_bytes() == (paths[1].parent/f'input.{suffix}').read_bytes()
    assert new['modes'].keys() == old['modes'].keys()
    count = 0
    for mode in new['modes']:
        for i in range(5):
            assert new['modes'][mode]['hashes'][i] == old['modes'][mode]['hashes'][i]
            count += len(old['modes'][mode]['hashes'][i])
            current, previous = new['modes'][mode]['runs'][i], old['modes'][mode]['runs'][i]
            assert {k:v for k,v in current.items() if k not in ('wall_ms','present_schedule_mode')} == {k:v for k,v in previous.items() if k != 'wall_ms'}
        assert checked[0]['modes'][mode]['native_qor'] == checked[1]['modes'][mode]['native_qor']
    proof_path = args.state_audit.resolve()
    proof = json.loads(proof_path.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert proof['status'] == 'five_repeat_present_schedule_paths_factors_and_versions_audited'
    assert proof['source_sha256'][str(paths[0])] == sha(paths[0])
    assert all(sha(Path(p)) == h for p,h in proof['source_sha256'].items())
    files = paths+[proof_path,Path(__file__).resolve(),Path(__file__).with_name('audit_rr_present_experiments.py').resolve()]
    report = dict(status='five_repeat_default_present_schedule_parent_compatibility_audited',
                  equal_common_artifacts=count, changed_sources=sorted(changed),
                  source_sha256={str(p):sha(p) for p in files},
                  scope='Exact five-repeat common deterministic outputs, counters and native quality; '
                        'independent default-factor/state replay required. No quality benefit, timing '
                        'runtime or physical hardware claim.', board_result=False,research_complete=False)
    assert not args.output.exists()
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],equal_common_artifacts=count)))
