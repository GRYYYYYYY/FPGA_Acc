"""Audit precision outcomes only after matching core sources, inputs and settings."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
from audit_rr_experiments import audit


def match_settings(fine, coarse, varying='cost_scale', expected=(256,1)):
    for field in ('case','reference','native_run_sha256','reference_sha256','timing_vpr','native_cost_export'):
        assert fine[field] == coarse[field], field
    assert fine['configuration'][varying] == expected[0]
    assert coarse['configuration'][varying] == expected[1]
    clean = lambda m: {k:v for k,v in m['configuration'].items() if k != varying}
    assert clean(fine) == clean(coarse), 'Another routing configuration changed'
    core = lambda m: {k:v for k,v in m['source_sha256'].items()
                       if Path(k).suffix in ('.cpp','.hpp','.h') or Path(k).name == 'CMakeLists.txt'}
    assert core(fine) == core(coarse) and core(fine), 'Core sources differ'
    assert fine['modes'].keys() == coarse['modes'].keys()
    def environments(m):
        result = {}
        for mode in m['modes']:
            for repeat in range(5):
                label = f'{mode}_{repeat}'
                step, = [s for s in m['steps'] if s['label'] == label]
                env = dict(step['routing_environment'])
                if varying == 'cost_scale':
                    assert env.pop('DIEROUTE_COST_SCALE') == str(m['configuration']['cost_scale'])
                elif varying == 'task_order':
                    assert env.pop('DIEROUTE_LOCAL_TASK_ORDER') == str(int(m['configuration']['task_order'] == 'local_distance'))
                elif varying == 'cleanup_passes':
                    assert env.pop('DIEROUTE_CLEANUP_PASSES') == str(m['configuration']['cleanup_passes'])
                elif varying == 'route_tree_timing_weight_q':
                    assert env.pop('DIEROUTE_TREE_TIMING_WEIGHT_Q') == str(m['configuration'][varying])
                elif varying == 'channel_span_price_q':
                    assert env.pop('DIEROUTE_CHANNEL_SPAN_PRICE_Q') == str(m['configuration'][varying])
                else:
                    raise ValueError('Unsupported comparison variable')
                command = shlex.split(env['PERSISTROUTE_TIMING_COMMAND'])
                assert len(command) == 2
                env['PERSISTROUTE_TIMING_COMMAND'] = hashlib.sha256(Path(command[1]).read_bytes()).hexdigest()
                result[label] = env
        return result
    assert environments(fine) == environments(coarse), 'Another routing environment setting changed'
    return len(core(fine))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fine',type=Path)
    parser.add_argument('coarse',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    verified = [audit(path.resolve()) for path in (args.fine,args.coarse)]
    manifests = [json.loads(path.read_text()) for path in (args.fine,args.coarse)]
    matched = match_settings(*manifests)
    for suffix in ('nodes','edges','resources','tasks'):
        arrays = [path.parent/('input.'+suffix) for path in (args.fine,args.coarse)]
        assert hashlib.sha256(arrays[0].read_bytes()).digest() == hashlib.sha256(arrays[1].read_bytes()).digest(),suffix
    outcomes = {}
    for mode in manifests[0]['modes']:
        outcomes[mode] = {}
        for scale, evidence in zip((256,1),verified):
            m = evidence['modes'][mode]
            outcomes[mode][str(scale)] = dict(status=m['status'],repeats=m['repeats_verified'],
                                             counters=m['counters'],native_qor=m.get('native_qor'))
    report = dict(status='same_source_precision_pair_audited',matched_core_files=matched,
                  outcomes=outcomes,scope='One development case, matched code/input/configuration with precision changed; no board or general QoR acceptance',
                  manifests_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.fine,args.coarse)},
                  board_result=False,research_complete=False)
    assert not args.output.exists(), 'Preserve existing comparisons'
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],matched_core_files=matched)))
