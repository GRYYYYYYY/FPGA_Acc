#!/usr/bin/env python3
"""Re-execute frozen TilePlace, then PR from empty routing on its fixed placement.

All output stays in FusionPAR. Native VPR legality-only routing publications are
baseline outputs, not QoR-improving FP moves. Budgets/objectives are reported.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from run_development import ROOT, execute, sha


def checked(entry):
    p = Path(entry['path'])
    if sha(p) != entry['sha256']:
        raise ValueError('changed reference: '+str(p))
    return p


def run(args):
    out = args.output.resolve()
    if out.exists():
        raise ValueError('output already exists')
    out.mkdir(parents=True)
    inventory_path = ROOT/'experiments/strong_baseline_inventory_2026-10-13.json'
    inventory = json.loads(inventory_path.read_text())
    checked(inventory['protocol'])
    reference = inventory['designs'][args.design]
    for entry in reference['evidence']:
        checked(entry)
    archive = ROOT.parent/'tileplace/experiments/implementation_sources'/inventory['tileplace_frozen_implementation']
    identity = json.loads((archive/'archive.json').read_text())
    # Verify content identity as well as each frozen source byte, independent
    # of the mutable TilePlace tools directory.
    expected_identity = {'parser': identity['parser'], 'sources': [
        {'name': e['name'], 'sha256': e['sha256']} for e in identity['sources']]}
    import hashlib
    encoded = json.dumps(expected_identity, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    if hashlib.sha256(encoded).hexdigest() != inventory['tileplace_frozen_implementation']:
        raise ValueError('frozen placer implementation identity mismatch')
    frozen = out/'frozen_placer';frozen.mkdir()
    for entry in identity['sources']:
        if Path(entry['name']).name != entry['name'] or sha(archive/entry['name']) != entry['sha256']:
            raise ValueError('frozen placer source mismatch')
        shutil.copyfile(archive/entry['name'], frozen/entry['name'])
    shutil.copyfile(archive/'archive.json', frozen/'archive.json')
    old_report = next(checked(e) for e in reference['evidence'] if Path(e['path']).name=='report.json')
    case = old_report.parent.parent
    placer = out/'placer'
    if args.reuse_placer:
        previous = args.reuse_placer.resolve()
        placer.symlink_to(previous/'placer', target_is_directory=True)
    else:
        placer.mkdir()
    command = json.loads((old_report.parent/'refinement_00.command.json').read_text())
    command[next(i for i,s in enumerate(command) if s.endswith('/run_tileplace_v2.py'))] = str(frozen/'run_tileplace_v2.py')
    for flag, value in {'--work': placer/'work', '--output-place': placer/'final.place',
                        '--report': placer/'report.json', '--timing-report': placer/'timing.json',
                        '--implementation-manifest': frozen/'archive.json'}.items():
        command[command.index(flag)+1] = str(value)
    if args.reuse_placer:
        placement_process = json.loads((previous/'placer_process.process.json').read_text())
        if placement_process['exit_status'] != 0:
            raise ValueError('cannot reuse an unsuccessful placer process')
        for entry in identity['sources']:
            if sha(previous/'frozen_placer'/entry['name']) != entry['sha256']:
                raise ValueError('reused placer source mismatch')
    else:
        placement_process = execute(command, out/'placer_process')
    report = json.loads((placer/'report.json').read_text())
    if report['status'] != 'pass' or not report['final']['legal']:
        raise ValueError('placer did not produce a legal final snapshot')
    if report['provenance']['implementation']['sha256'] != inventory['tileplace_frozen_implementation']:
        raise ValueError('executed placer implementation differs')
    for entry in report['provenance']['inputs']:
        checked(entry)
    final_native = checked({'path': report['final']['report_path'], 'sha256': report['final']['report_sha256']})
    closure = json.loads(final_native.read_text())
    route = checked(closure['outputs']['route'])
    canonical_place = route.parent/'vpr_input.place'
    if 'Placement_ID: SHA256:'+sha(canonical_place) not in route.read_text().splitlines()[0]:
        raise ValueError('placer route and canonical placement differ')
    original_net = case/'baseline'/f'{args.design}.net'
    if sha(route.parent/'vpr_input.net') != sha(original_net):
        raise ValueError('placer changed packed netlist identity')
    # Same graph/pin contract, freshly remapped to the reproduced placement.
    remapped = out/'case';baseline = remapped/'baseline';baseline.mkdir(parents=True)
    links = {f'{args.design}.net': original_net, f'{args.design}.place': canonical_place,
             f'{args.design}.route': route, 'rr_graph.xml': case/'baseline/rr_graph.xml'}
    for name, target in links.items():
        (baseline/name).symlink_to(target.resolve())
    (remapped/'inputs').symlink_to((case/'inputs').resolve(), target_is_directory=True)
    vtr = ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    routing_command = [sys.executable, str(ROOT/'tools/run_development.py'), '--case-root', str(remapped),
        '--design', args.design, '--vpr', str(vtr/'build_tileplace_vpr/vpr/vpr'),
        '--timing-vpr', str(vtr/'build_tileplace_vpr_timing_optional/vpr/vpr'),
        '--arch', str(vtr/'vtr_flow/arch/timing/k6_frac_N10_mem32K_40nm.xml'),
        '--circuit', str(vtr/'vtr_flow/benchmarks/blif'/f'{args.design}.blif'),
        '--output', str(out/'routing'), '--attempts', '1', '--repeats', str(args.repeats),
        '--priority-reference', str(args.priority_reference.resolve()), '--modes', 'route_only']
    print(f'{args.design}: frozen placer complete; starting fixed-placement PR', flush=True)
    routing_process = execute(routing_command, out/'routing_process')
    audit_path = out/'publication_audit.json'
    execute([sys.executable, ROOT/'tools/audit_development.py', out/'routing', '--output', audit_path], out/'publication_audit_process')
    routing = json.loads((out/'routing/audit.json').read_text())
    audits = json.loads(audit_path.read_text())
    for entry in identity['sources']:
        if sha(frozen/entry['name']) != entry['sha256']:
            raise ValueError('frozen placer source changed during execution')
    original = json.loads((case/'baseline/baseline.json').read_text())
    rows = []
    for record in routing['records']:
        completed = record['summary']['commits']==1
        quality = record['final_native_quality'] if completed else None
        rows.append({'repeat': record['repeat'], 'completed_PR_route': completed,
                     'quality': None if quality is None else {k:quality[k] for k in ('wirelength','cpd_ns')},
                     'within_original_2pct_gate': completed and quality['wirelength']<=original['wirelength']*1.02 and quality['cpd_ns']<=original['cpd_ns']*1.02,
                     'placer_wall_ns': placement_process['wall_ns'],
                     'conversion_plus_PR_wall_ns': record['charged_wall_ns'],
                     'charged_placer_plus_PR_wall_ns': placement_process['wall_ns']+record['charged_wall_ns'],
                     'event_status': [e['status'] for e in record['event_semantics']]})
    files = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and
             'build' not in p.relative_to(out).parts and 'sources' not in p.relative_to(out).parts and
             'case' not in p.relative_to(out).parts}
    result = {'schema':'FUSIONPAR_FROZEN_TP_PR_BASELINE_V1', 'design':args.design,
              'placer_reexecuted':True, 'placer_repeats':1, 'PR_repeats':args.repeats,
              'placer_reused_from_this_session':str(previous) if args.reuse_placer else None,
              'placer_implementation':inventory['tileplace_frozen_implementation'],
              'placer_matches_historical_final_place':sha(placer/'final.place')==sha(old_report.parent/'final.place'),
              'placer_quality':{k:report['final'][k] for k in ('wirelength','cpd_ns')},
              'placer_closures':report['closure_calls'], 'PR_deterministic':routing['deterministic'],
              'publication_audit':audits, 'rows':rows, 'artifacts':files,
              'pipeline_inputs':[{'path':str(p),'sha256':sha(p)} for p in (inventory_path,Path(__file__).resolve(),old_report,case/'baseline/baseline.json',args.priority_reference.resolve())],
              'placer_process':placement_process,
              'placer_artifacts':{str(p.resolve()):sha(p) for p in sorted(placer.resolve().rglob('*')) if p.is_file()},
              'limits':['One current placer run reused for repeated PR stage; not repeated full pipelines',
                        '24 TP native closures vs FP three primary proposals; objectives/budgets differ',
                        'The TP stage already uses native VPR routing feedback',
                        'Charged cost includes reproduced TP wall time plus conversion and PR host wall time; builds reported separately',
                        'No independent FusionPAR speedup or FPGA performance claim']}
    (out/'pipeline.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'design':args.design,'placer_quality':result['placer_quality'],'PR_rows':rows},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',choices=('ex5p','alu4','misex3'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=5)
    p.add_argument('--priority-reference',type=Path,required=True)
    p.add_argument('--reuse-placer',type=Path,help='Reuse a verified successful placer stage from an earlier attempt in this session, charging its full measured cost')
    args=p.parse_args()
    if args.repeats<1:p.error('positive repeat count required')
    run(args)
