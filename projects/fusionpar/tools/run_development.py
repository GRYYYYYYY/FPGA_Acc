#!/usr/bin/env python3
"""Build and archive a frozen same-component local-refinement development suite.

No held-out or speedup claim is inferred. All native validation and rejected work
remain in each subprocess wall time. Input conversion is a separately measured
common cost charged equally to every mode's comparison total.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MODES = ('sequential', 'sequential_shared', 'interleaved', 'interleaved_repair')
ALL_MODES = MODES + ('interleaved_tree_control', 'interleaved_tree_reuse', 'interleaved_tree_feedback', 'sequential_tree_reuse', 'sequential_shared_tree_reuse', 'interleaved_placement_repair', 'protocol_probe', 'route_only')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def execute(command, output, cwd=ROOT):
    start = time.monotonic_ns()
    with output.with_suffix('.stdout.log').open('w') as stdout, output.with_suffix('.stderr.log').open('w') as stderr:
        result = subprocess.run(list(map(str, command)), cwd=cwd, stdout=stdout, stderr=stderr)
    report = {'command': list(map(str, command)), 'cwd': str(cwd), 'exit_status': result.returncode,
              'wall_ns': time.monotonic_ns()-start,
              'stdout_sha256': sha(output.with_suffix('.stdout.log')), 'stderr_sha256': sha(output.with_suffix('.stderr.log'))}
    output.with_suffix('.process.json').write_text(json.dumps(report, indent=2)+'\n')
    if result.returncode:
        raise RuntimeError(f'command failed: {output}')
    return report


def run(args):
    modes = MODES + (('interleaved_tree_control', 'interleaved_tree_reuse') if args.tree_reuse else ()) + (('interleaved_placement_repair',) if args.placement_repair else ()) + (('protocol_probe',) if args.protocol_probe else ())
    if args.modes:
        modes = tuple(args.modes)
    out = args.output.resolve()
    if out.exists():
        raise ValueError('output already exists')
    out.mkdir(parents=True)
    sources = sorted([ROOT/'CMakeLists.txt', *ROOT.glob('include/*.hpp'), *ROOT.glob('src/*.cpp'),
                      *ROOT.glob('host/*.cpp'), *ROOT.glob('tb/*.cpp'), *ROOT.glob('tb/*.py'), *ROOT.glob('tools/*.py'),
                      *ROOT.parent.glob('persistroute/include/*.hpp'), *ROOT.parent.glob('persistroute/src/*.cpp')])
    source_bindings = []
    snapshot = out/'sources'
    for path in sources:
        relative = path.relative_to(ROOT.parent)
        dest = snapshot/relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        source_bindings.append({'path': str(path), 'snapshot': str(dest), 'sha256': sha(dest)})
    build = out/'build'
    execute(['cmake', '-S', ROOT, '-B', build, '-DCMAKE_BUILD_TYPE=Release'], out/'configure')
    execute(['cmake', '--build', build, '-j', str(args.jobs)], out/'build_command')
    tests = execute(['ctest', '--test-dir', build, '--output-on-failure'], out/'tests')
    case = args.case_root.resolve()
    name = args.design
    baseline, inputs = case/'baseline', case/'inputs'
    bundle = out/'bundle'
    prepare_command = [sys.executable, ROOT/'tools/prepare_vpr_bundle.py',
        '--net', baseline/f'{name}.net', '--place', baseline/f'{name}.place', '--route', baseline/f'{name}.route',
        '--graph', baseline/'rr_graph.xml', '--graph-prefix', inputs/'vpr_input', '--contract', inputs/'contract',
        '--vpr', args.vpr.resolve(), '--arch', args.arch.resolve(), '--circuit', args.circuit.resolve(),
        '--channel-width', str(args.channel_width), '--output', bundle]
    if args.timing_vpr:
        prepare_command += ['--timing-vpr', args.timing_vpr.resolve()]
    if args.priority_reference:
        prepare_command += ['--priority-reference', args.priority_reference.resolve()]
    prepare_command += ['--rr-export-backend', args.rr_export_backend]
    prepare = execute(prepare_command, out/'prepare')
    host = build/'fusionpar_host'
    records = []
    for repeat in range(args.repeats):
        order = modes[repeat % len(modes):] + modes[:repeat % len(modes)]
        for mode in order:
            prefix = out/f'{mode}_{repeat}'
            process = execute([host, bundle, prefix, mode, str(args.attempts), ROOT/'tools/validate_candidate.py',
                               str(args.tree_timing_weight_q)], out/f'process_{mode}_{repeat}')
            summary = json.loads((prefix/'summary.json').read_text())
            events = [json.loads(row) for row in (prefix/'events.jsonl').read_text().splitlines()]
            reports = [json.loads(path.read_text()) for path in sorted(prefix.glob('validation_*/validation.json'))]
            final_sha = sha(prefix/'final.state')
            from validate_candidate import physical_digest, read_state
            final_physical = physical_digest(read_state(prefix/'final.state'))
            final_reports = [r for r in reports if r['physical_state_sha256'] == final_physical]
            if not final_reports or not all(r['legal'] for r in reports):
                raise RuntimeError('final state lacks native legal certificate')
            timing_events = [json.loads(row) for row in (prefix/'timing.jsonl').read_text().splitlines()]
            if args.timing_vpr:
                timing = final_reports[-1]['timing']
                if not timing or not timing_events or summary['timing_epoch'] != len(timing_events):
                    raise RuntimeError('missing timing barrier evidence')
                text = Path(timing['criticalities_path'])
                if sha(text) != timing['criticalities_sha256']:
                    raise RuntimeError('timing snapshot binding changed')
                values = list(map(int, text.read_text().split()))
                if values[0] != len(values)-1 or values[1:] != read_state(prefix/'final.state')[4]:
                    raise RuntimeError('final state did not consume native criticalities')
            if any(e['before'] != e['after'] for e in events if e['status'] != 'committed'):
                raise RuntimeError('rejected transaction mutated authoritative state')
            record = {'mode': mode, 'repeat': repeat, 'directory': str(prefix), 'summary': summary,
                      'process': process, 'common_conversion_ns': prepare['wall_ns'],
                      'charged_wall_ns': process['wall_ns'] + prepare['wall_ns'],
                      'final_state_sha256': final_sha, 'final_physical_sha256': final_physical, 'final_native_quality': final_reports[-1],
                      'timing_events': timing_events,
                      'event_semantics': [{k: e[k] for k in ('proposal', 'status', 'before', 'after', 'candidate_digest', 'affected_nets', 'affected_connections', 'expanded', 'phase', 'repair_index', 'moves', 'feedback_kind', 'feedback_connections', 'feedback_resources', 'retained_connections', 'kernel_searches') if k in e} for e in events]}
            records.append(record)
            (out/'partial.json').write_text(json.dumps(records, indent=2)+'\n')
            print(f"{mode} repeat={repeat} commits={summary['commits']} aborts={summary['aborts']} wall_s={process['wall_ns']/1e9:.3f}", flush=True)
    for entry in source_bindings:
        if sha(entry['path']) != entry['sha256']:
            raise ValueError('implementation changed during suite: '+entry['path'])
    deterministic = None if args.repeats < 2 else all(len({r['final_state_sha256'] for r in records if r['mode'] == mode}) == 1 and
                        len({json.dumps(r['event_semantics'], sort_keys=True) for r in records if r['mode'] == mode}) == 1
                        and len({json.dumps(r['timing_events'], sort_keys=True) for r in records if r['mode'] == mode}) == 1
                        for mode in modes)
    sharing_equivalent = None
    if 'sequential' in modes and 'sequential_shared' in modes:
        cold = next(r for r in records if r['mode'] == 'sequential')
        shared = next(r for r in records if r['mode'] == 'sequential_shared')
        sharing_equivalent = cold['final_state_sha256'] == shared['final_state_sha256'] and cold['event_semantics'] == shared['event_semantics']
    tree_equivalent = None
    retained_sharing_equivalent = None
    if 'sequential_tree_reuse' in modes and 'sequential_shared_tree_reuse' in modes:
        retained_sharing_equivalent = all(
            next(r for r in records if r['mode']=='sequential_tree_reuse' and r['repeat']==i)['event_semantics'] ==
            next(r for r in records if r['mode']=='sequential_shared_tree_reuse' and r['repeat']==i)['event_semantics'] and
            next(r for r in records if r['mode']=='sequential_tree_reuse' and r['repeat']==i)['final_state_sha256'] ==
            next(r for r in records if r['mode']=='sequential_shared_tree_reuse' and r['repeat']==i)['final_state_sha256']
            for i in range(args.repeats))
    if 'interleaved_tree_control' in modes and 'interleaved' in modes:
        tree_equivalent = all(
            next(r for r in records if r['mode']=='interleaved' and r['repeat']==i)['event_semantics'] ==
            next(r for r in records if r['mode']=='interleaved_tree_control' and r['repeat']==i)['event_semantics']
            for i in range(args.repeats))
    artifacts = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and
                 'build' not in p.relative_to(out).parts and 'sources' not in p.relative_to(out).parts and p.name != 'audit.json'}
    feedback_budget_matched = None
    if 'interleaved_tree_feedback' in modes and 'interleaved_tree_reuse' in modes:
        feedback_budget_matched = all(
            len(r['event_semantics']) == r['summary']['evaluations'] == r['summary']['evaluation_budget'] == args.attempts
            for r in records if r['mode'] in ('interleaved_tree_feedback', 'interleaved_tree_reuse'))
    audit = {'schema': 'FUSIONPAR_DEVELOPMENT_AUDIT_V1', 'design': name,
             'host_sha256': sha(host), 'sources': source_bindings, 'tests': tests,
             'environment': {'platform': platform.platform(), 'python': sys.version},
             'repeats': args.repeats, 'attempts': args.attempts, 'records': records,
             'route_tree_timing_weight_q': args.tree_timing_weight_q,
             'validation_cost_profile': 'FUSIONPAR_VALIDATION_COST_V1',
             'rr_export_backend': args.rr_export_backend,
             'deterministic': deterministic, 'sequential_shared_equivalent': sharing_equivalent,
             'tree_control_equivalent_to_pr': tree_equivalent,
             'retained_sequential_shared_equivalent': retained_sharing_equivalent,
             'feedback_evaluation_budget_matched': feedback_budget_matched,
             'has_native_validated_move_commit': any(r['summary']['commits'] for r in records if r['mode'] != 'route_only'),
             'has_qor_accepted_move_commit': any(r['summary']['commits'] for r in records if r['mode'] not in ('protocol_probe','route_only')),
             'artifacts': artifacts,
             'limits': ['development design only', 'local refinement from a legal routed baseline',
                        'native timing barriers enabled' if args.timing_vpr else 'frozen zero criticalities; STA checks QoR only',
                        'strict WL/CPD lexicographic acceptance with 2% initial native CPD guard',
                        'same simple move generator, not best placer+PR baseline', 'RC bypassed, no U280 execution',
                        'protocol_probe is native-legality-only correctness evidence and excluded from protected QoR/performance comparison',
                        'copy_payload_bytes excludes PR internal scratch allocations and is not measured HBM/PCIe traffic']}
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    if deterministic is False or sharing_equivalent is False or tree_equivalent is False or retained_sharing_equivalent is False:
        raise RuntimeError('determinism/equivalence check failed')
    return {'audit': str(out/'audit.json'), 'deterministic': deterministic,
            'has_native_validated_move_commit': audit['has_native_validated_move_commit']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('case-root', 'vpr', 'arch', 'circuit', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--design', required=True)
    p.add_argument('--channel-width', type=int, default=200)
    p.add_argument('--repeats', type=int, default=5)
    p.add_argument('--attempts', type=int, default=3)
    p.add_argument('--jobs', type=int, default=8)
    p.add_argument('--timing-vpr', type=Path)
    p.add_argument('--priority-reference', type=Path)
    p.add_argument('--rr-export-backend', choices=('xml', 'sqlite'), default='xml')
    p.add_argument('--tree-timing-weight-q', type=int, default=0,
                   help='Q8 upstream route-tree delay weight, 0..256; default preserves historical behavior')
    p.add_argument('--protocol-probe', action='store_true')
    p.add_argument('--placement-repair', action='store_true')
    p.add_argument('--tree-reuse', action='store_true')
    p.add_argument('--modes', nargs='+', choices=ALL_MODES, help='Explicit focused comparison; overrides optional mode flags')
    args = p.parse_args()
    if args.repeats < 1 or args.attempts < 1 or args.jobs < 1:
        p.error('positive repeats/attempts/jobs required')
    if not 0 <= args.tree_timing_weight_q <= 256:
        p.error('tree timing weight must be 0..256')
    if args.modes and len(set(args.modes)) != len(args.modes):
        p.error('duplicate modes')
    print(json.dumps(run(args), indent=2))
