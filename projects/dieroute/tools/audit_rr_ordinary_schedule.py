"""Combine five-repeat native checks with independent ordinary schedule/version replay."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit
from rr_ordinary_schedule_replay import replay
import audit_rr_experiments
import rr_ordinary_schedule_replay


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    pair = args.pair.resolve()
    manifest = json.loads(pair.read_text())
    cfg = manifest['configuration']
    assert cfg['ordinary_schedule_mode'] in (0, 1, 2)
    assert cfg['cost_state_bits'] == 64 and cfg['timing_updates'] and cfg['task_order'] == 'preserve'
    assert cfg['criticality_feedback_threshold_q'] == 0 and not cfg['feedback_local_delay_guard']
    assert not cfg['supplemental_transaction_mode'] and not cfg['speculative_workers'] and not cfg['cleanup_passes']
    assert 'native_cost_export' in manifest and cfg['cost_model'] == 'vpr_style'
    header = pair.parent / 'source/persistroute/include/pathfinder.hpp'
    text = header.read_text()
    for field in ('present_start_q = 256', 'present_multiplier_q = 512', 'history_increment_q = 256'):
        assert field in text
    verified = audit(pair)
    files = [pair, Path(__file__), Path(audit_rr_experiments.__file__),
             Path(rr_ordinary_schedule_replay.__file__), header]
    sources = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    modes = {}
    for mode, proof in verified['modes'].items():
        assert proof['repeats_verified'] == 5 and not proof['counters']['edge_identity']
        for i in range(5):
            step, = [s for s in manifest['steps'] if s['label'] == f'{mode}_{i}']
            env = step['routing_environment']
            assert env['DIEROUTE_ORDINARY_SCHEDULE_MODE'] == str(cfg['ordinary_schedule_mode'])
            assert env['DIEROUTE_TIMING_UPDATE_PERIOD'] == '1'
            assert manifest['modes'][mode]['runs'][i]['ordinary_schedule_mode'] == cfg['ordinary_schedule_mode']
        result = replay(pair.parent / 'input', pair.parent / f'{mode}_0', cfg['ordinary_schedule_mode'],
                        cfg['issue_width'], cfg['min_timing_iterations'], cfg['cost_scale'],
                        cfg['route_tree_timing_weight_q'], cfg['criticality_cap_q'])
        assert result['cpu_legal'] == bool(proof['counters']['legal'])
        assert result['epochs'] == proof['counters']['iterations'] <= cfg['max_iterations']
        if not result['cpu_legal']:
            assert result['epochs'] == cfg['max_iterations']
        assert result['ripup_events'] == proof['counters']['ordinary_ripup_events']
        sources.update(result.pop('source_sha256'))
        modes[mode] = result
    report = dict(status='five_repeat_ordinary_schedule_paths_ripups_and_versions_audited', modes=modes,
                  source_sha256=sources,
                  scope='Generic frozen-source/native/determinism checks plus independently reconstructed '
                        'ordinary dispatch, incumbent ripups, selected seeds/branches, pending masks, timing-input '
                        'delays, epoch hashes and final resource/cost bytes. Fixed default cost coefficients. '
                        'No per-CU read-version receipt, independent search-work oracle, physical performance '
                        'or global quality acceptance claim.', board_result=False, research_complete=False)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], modes=modes)))
