#!/usr/bin/env python3
"""Run and audit a fresh nine-closure frozen-TP strong reference, five times."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import time

from audit_development import require
from prepare_vpr_bundle import endpoints, tp
from run_development import ROOT, execute, sha
from validate_candidate import native


def binding(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def checked(entry):
    path = Path(entry['path']).resolve()
    require(sha(path) == entry['sha256'], 'changed reference: ' + str(path))
    return path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def inspect_run(directory, budget):
    report_path = directory / 'report.json'
    report = json.loads(report_path.read_text())
    require(report['status'] == 'pass' and report['closure_budget'] == budget,
            'unexpected TP status/budget')
    require(report['closure_calls'] == len(report['trials']) == budget,
            'TP did not consume the common evaluation budget')
    require([t['trial'] for t in report['trials']] == list(range(1, budget + 1)),
            'missing or duplicate TP trial')
    for entry in report['provenance']['inputs']:
        checked(entry)
    process = json.loads((directory / 'process.process.json').read_text())
    require(process['exit_status'] == 0, 'TP subprocess failed')
    for stream in ('stdout', 'stderr'):
        require(sha(directory / ('process.' + stream + '.log')) == process[stream + '_sha256'],
                'TP process log changed')
    command = process['command']
    contract = Path(command[command.index('--contract') + 1])
    baseline_path = Path(command[command.index('--baseline-closure') + 1])
    original = json.loads(baseline_path.read_text())
    baseline_place = Path(command[command.index('--input-place') + 1])
    baseline_net = Path(command[command.index('--netlist') + 1])
    net_sha = sha(baseline_net)
    baseline_route = checked(original['outputs']['route'])
    require(original['status'] == 'pass' and original['legal'], 'illegal original baseline')
    base_cpd = Decimal(str(original['cpd_ns']))
    rows = [{'trial': 0, 'legal': True, 'eligible': True, 'tp_accepted': None,
             'wirelength': original['wirelength'], 'cpd_ns': original['cpd_ns'],
             'artifacts': {k: binding(p) for k, p in
                           (('place', baseline_place), ('net', baseline_net), ('route', baseline_route))}}]
    semantics = []
    for trial in report['trials']:
        record = trial['closure']
        proposal = checked(trial['candidate_place'])
        row = {'trial': trial['trial'], 'tp_accepted': trial['accepted'],
               'legal': record.get('legal', False), 'eligible': False,
               'wirelength': record.get('wirelength'), 'cpd_ns': record.get('cpd_ns')}
        semantic = {k: trial[k] for k in ('trial', 'accepted', 'reason', 'transactions')}
        semantic['proposal'] = endpoints.placements(proposal, net_sha)
        if record.get('report_path'):
            closure_path = checked({'path': record['report_path'], 'sha256': record['report_sha256']})
            closure = json.loads(closure_path.read_text())
            for group in ('inputs', 'outputs'):
                for entry in closure[group].values():
                    if entry is not None:
                        checked(entry)
            for key in ('legal', 'wirelength', 'cpd_ns', 'returncode'):
                require(record.get(key) == closure.get(key), 'closure summary mismatch')
            row['closure'] = binding(closure_path)
        else:
            require(not row['legal'], 'legal trial missing native certificate')
            closure = None
        if row['legal']:
            require(closure['returncode'] == 0, 'legal closure failed')
            markers, wl, cpd = native.parse_vpr_output(checked(closure['outputs']['stdout']).read_text())
            require(all(markers[k] for k in ('routing_consistency', 'successfully_routed', 'vpr_succeeded')),
                    'native success/consistency marker missing')
            require(wl == row['wirelength'] and Decimal(str(cpd)) == Decimal(str(row['cpd_ns'])),
                    'native log quality disagrees')
            artifacts = {k: closure['outputs'][v] for k, v in
                         (('net', 'vpr_netlist_copy'), ('place', 'vpr_place_copy'), ('route', 'route'))}
            require(artifacts['net']['sha256'] == net_sha, 'packed netlist changed')
            place = checked(artifacts['place'])
            route_lines = checked(artifacts['route']).read_text().splitlines()
            require('Placement_ID: SHA256:' + sha(place) in route_lines[0], 'route/place identity mismatch')
            require(closure['placement_validation']['legal'] and
                    closure['placement_validation']['placement_sha256'] == sha(place),
                    'native certificate binds another canonical placement')
            row['contract_check'] = tp.validate_contract(contract, place)
            require(closure['inputs']['golden_place']['sha256'] == trial['candidate_place']['sha256'],
                    'native closure evaluated another proposal')
            require(endpoints.placements(place, net_sha) == semantic['proposal'],
                    'native closure changed placement coordinates or identity')
            row['artifacts'] = artifacts
            row['eligible'] = wl * 100 <= original['wirelength'] * 102 and Decimal(str(cpd)) <= base_cpd * Decimal('1.02')
            # Only the first route header contains the run-specific placement
            # path. All native routing lines, net IDs and nodes remain compared.
            semantic['route_body_sha256'] = digest(route_lines[1:])
        semantic['quality'] = {k: row[k] for k in ('legal', 'wirelength', 'cpd_ns', 'eligible')}
        semantics.append(semantic)
        rows.append(row)
    tp.validate_contract(contract, baseline_place)
    require('Placement_ID: SHA256:' + sha(baseline_place) in baseline_route.read_text().splitlines()[0],
            'baseline placement/route mismatch')
    selected = min((r for r in rows if r['eligible']),
                   key=lambda r: (r['wirelength'], Decimal(str(r['cpd_ns'])), r['trial']))
    return {'report': binding(report_path), 'process': binding(directory / 'process.process.json'),
            'implementation': report['provenance']['implementation']['sha256'],
            'closure_calls': report['closure_calls'], 'TP_final': report['final'],
            'population': rows, 'selected': selected, 'semantics_sha256': digest(semantics),
            'wall_seconds': process['wall_ns'] / 1e9}


def run(out):
    require(not out.exists(), 'output already exists')
    protocol_path = ROOT / 'experiments/tp_budget_reference_protocol_2026-10-13.json'
    protocol = json.loads(protocol_path.read_text())
    prior_path = ROOT / 'experiments/tp_checkpoint_reference_status_2026-10-13.json'
    prior = json.loads(prior_path.read_text())
    bindings = [binding(protocol_path), binding(prior_path), binding(Path(__file__))]
    out.mkdir(parents=True)
    frozen = out / 'frozen_placer'
    archive = ROOT.parent / 'tileplace/experiments/implementation_sources' / protocol['implementation']
    identity = json.loads((archive / 'archive.json').read_text())
    expected = {'parser': identity['parser'], 'sources': [
        {'name': e['name'], 'sha256': e['sha256']} for e in identity['sources']]}
    encoded = json.dumps(expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    require(hashlib.sha256(encoded).hexdigest() == protocol['implementation'], 'frozen source identity mismatch')
    frozen.mkdir()
    for entry in identity['sources']:
        require(Path(entry['name']).name == entry['name'] and sha(archive / entry['name']) == entry['sha256'],
                'bad frozen source')
        shutil.copyfile(archive / entry['name'], frozen / entry['name'])
    shutil.copyfile(archive / 'archive.json', frozen / 'archive.json')
    commands = {}
    for design in protocol['designs']:
        pipeline_path = checked(next(e for e in prior['designs'][design]['evidence']
                                     if Path(e['path']).name == 'pipeline.json'))
        pipeline = json.loads(pipeline_path.read_text())
        require(pipeline['placer_implementation'] == protocol['implementation'], 'different TP implementation')
        commands[design] = pipeline['placer_process']['command']
        bindings.append(binding(pipeline_path))
    for repeat in range(protocol['repeats']):
        order = protocol['designs'][repeat % 3:] + protocol['designs'][:repeat % 3]
        for design in order:
            directory = out / design / str(repeat)
            directory.mkdir(parents=True)
            command = commands[design][:]
            index = next(i for i, v in enumerate(command) if v.endswith('/run_tileplace_v2.py'))
            command[index] = str(frozen / 'run_tileplace_v2.py')
            for flag, value in {'--work': directory / 'work', '--output-place': directory / 'final.place',
                                '--report': directory / 'report.json', '--timing-report': directory / 'timing.json',
                                '--implementation-manifest': frozen / 'archive.json',
                                '--max-closures': protocol['closure_budget']}.items():
                command[command.index(flag) + 1] = str(value)
            print(f'Start {design} repeat {repeat}, budget {protocol["closure_budget"]}', flush=True)
            execute(command, directory / 'process')
            print(f'Complete {design} repeat {repeat}', flush=True)
    start = time.monotonic()
    results = {}
    for design in protocol['designs']:
        rows = [inspect_run(out / design / str(i), protocol['closure_budget'])
                for i in range(protocol['repeats'])]
        require(all(r['implementation'] == protocol['implementation'] for r in rows), 'executed source identity differs')
        require(len({r['semantics_sha256'] for r in rows}) == 1, 'repeated TP trajectories differ')
        require(len({(r['selected']['trial'], r['selected']['wirelength'], r['selected']['cpd_ns']) for r in rows}) == 1,
                'selected reference differs across repeats')
        results[design] = {'deterministic': True, 'runs': rows}
        print(f'Audited {design}: {len(rows)} deterministic runs', flush=True)
    for entry in identity['sources']:
        require(sha(frozen / entry['name']) == entry['sha256'], 'frozen source changed during study')
    for entry in bindings:
        checked(entry)
    result = {'schema': 'FUSIONPAR_TP_NINE_CLOSURE_REFERENCE_V1', 'pass': True,
              'bindings': bindings, 'protocol': protocol, 'designs': results,
              'postmeasurement_audit_seconds': time.monotonic() - start,
              'limits': protocol['limits']}
    (out / 'study.json').write_text(json.dumps(result, indent=2) + '\n')
    print('All 15 fresh nine-closure runs and native/contract/determinism audits passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.output.resolve())
