#!/usr/bin/env python3
"""Execute the preregistered six-input FP validation, retaining coverage failures."""
import argparse
import json
from pathlib import Path
import shutil
import sys

from audit_development import audit, require
from run_development import ROOT, execute, sha


def binding(path):
    return {'path': str(path.resolve()), 'sha256': sha(path)}


def unchanged(entries):
    for entry in entries:
        require(sha(entry['path']) == entry['sha256'], 'frozen file changed: ' + entry['path'])


def run(out):
    require(not out.exists(), 'output already exists')
    protocol_path = ROOT / 'experiments/independent_validation_protocol_2026-10-13.json'
    protocol = json.loads(protocol_path.read_text())
    case_root = (ROOT / protocol['input_root']).resolve()
    available = sorted(p.name for p in case_root.iterdir() if p.is_dir() and
                       all((p / name).is_file() for name in
                           ('baseline/baseline.json', 'inputs/contract/manifest.json', 'inputs/vpr_input.nodes')) and
                       p.name not in protocol['development_exclusions'])
    require(available == protocol['designs'], 'input population differs from preregistration')
    require(protocol['repeats'] == 5 and protocol['fixed_policy']['rr_export_backend'] == 'xml' and
            protocol['fixed_policy']['tree_timing_weight_q'] == 0, 'unexpected frozen policy')
    vtr = ROOT.parent / 'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    vpr = vtr / 'build_tileplace_vpr/vpr/vpr'
    timing_vpr = vtr / 'build_tileplace_vpr_timing_optional/vpr/vpr'
    arch = vtr / 'vtr_flow/arch/timing/k6_frac_N10_mem32K_40nm.xml'
    sources = sorted([ROOT / 'CMakeLists.txt', *ROOT.glob('include/*.hpp'), *ROOT.glob('src/*.cpp'),
                      *ROOT.glob('host/*.cpp'), *ROOT.glob('tb/*.cpp'), *ROOT.glob('tb/*.py'),
                      *ROOT.glob('tools/*.py'), *ROOT.parent.glob('persistroute/include/*.hpp'),
                      *ROOT.parent.glob('persistroute/src/*.cpp')])
    # The converter/validator imports these sibling Python helpers. Record them
    # for the whole cohort as well as the per-bundle runtime source bindings.
    helpers = sorted(p for project in ('persistroute', 'tileplace', 'routecast')
                     for p in (ROOT.parent / project / 'tools').glob('*.py'))
    frozen = [binding(p) for p in [protocol_path, *sources, *helpers]]
    inputs = [binding(p) for p in (vpr, timing_vpr, arch)]
    for design in available:
        case = case_root / design
        names = [f'baseline/{design}.{suffix}' for suffix in ('net', 'place', 'route')]
        names += ['baseline/baseline.json', 'baseline/rr_graph.xml']
        names += ['inputs/vpr_input.' + suffix for suffix in ('manifest.json', 'nodes', 'edges', 'resources')]
        paths = [case / name for name in names]
        paths += sorted(p for p in (case / 'inputs/contract').iterdir() if p.is_file())
        paths.append(vtr / 'vtr_flow/benchmarks/blif' / (design + '.blif'))
        inputs += [binding(p) for p in paths]
    out.mkdir(parents=True)
    for entry in frozen:
        path = Path(entry['path'])
        dest = out / 'sources' / path.relative_to(ROOT.parent)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        require(sha(dest) == entry['sha256'], 'source changed during freeze')
    freeze = {'schema': 'FUSIONPAR_VALIDATION_COHORT_FREEZE_V1', 'sources': frozen, 'inputs': inputs}
    (out / 'freeze.json').write_text(json.dumps(freeze, indent=2) + '\n')
    rows = []
    for index, design in enumerate(available):
        # Rotate track order between designs; each development runner rotates
        # its mode order between repeats. No audit work overlaps measurements.
        tracks = protocol['tracks'][index % 2:] + protocol['tracks'][:index % 2]
        for track in tracks:
            unchanged(frozen)
            directory = out / design / track['id']
            directory.parent.mkdir(parents=True, exist_ok=True)
            command = [sys.executable, ROOT / 'tools/run_development.py', '--case-root', case_root / design,
                       '--design', design, '--vpr', vpr, '--timing-vpr', timing_vpr, '--arch', arch,
                       '--circuit', vtr / 'vtr_flow/benchmarks/blif' / (design + '.blif'),
                       '--output', directory, '--rr-export-backend', 'xml', '--tree-timing-weight-q', '0',
                       '--attempts', str(track['attempts']), '--repeats', '5', '--modes', *track['modes']]
            prefix = directory.parent / (track['id'] + '_process')
            print(f'Start {design} {track["id"]}', flush=True)
            try:
                process = execute(command, prefix)
                completed = True
            except RuntimeError:
                # A failed converter/native run is retained in the denominator.
                # It does not authorize a policy change or a replacement input.
                process = json.loads(prefix.with_suffix('.process.json').read_text())
                completed = False
            row = {'design': design, 'track': track['id'], 'directory': str(directory),
                   'completed': completed, 'process': process, 'audited': False}
            rows.append(row)
            (out / 'execution_progress.json').write_text(json.dumps(rows, indent=2) + '\n')
            print(f'Finished {design} {track["id"]}: completed={completed}', flush=True)
    unchanged(frozen)
    unchanged(inputs)
    for row in rows:
        if not row['completed']:
            continue
        directory = Path(row['directory'])
        try:
            result = audit(directory)
            path = directory / 'publication_audit.json'
            path.write_text(json.dumps(result, indent=2) + '\n')
            row['publication_audit'] = binding(path)
            row['audited'] = True
        except (ValueError, KeyError, OSError) as error:
            row['audit_failure'] = f'{type(error).__name__}: {error}'
        print(f'Audit {row["design"]} {row["track"]}: {row["audited"]}', flush=True)
    unchanged(frozen)
    unchanged(inputs)
    result = {'schema': 'FUSIONPAR_INDEPENDENT_VALIDATION_EXECUTION_V1',
              'all_suites_passed': all(r['completed'] and r['audited'] for r in rows),
              'selected_design_count': len(available), 'expected_suite_count': 12,
              'protocol': binding(protocol_path), 'freeze': binding(out / 'freeze.json'),
              'rows': rows, 'limits': protocol['limits']}
    require(len(rows) == 12, 'incomplete selected cohort execution')
    (out / 'study.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'all_suites_passed': result['all_suites_passed'], 'suite_count': len(rows)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve())
