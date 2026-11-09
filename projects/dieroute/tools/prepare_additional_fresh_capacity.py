"""Prepare unchanged capacity repair and native checks for a fresh parent."""
import argparse
import json
from pathlib import Path
import sys
from prepare_additional_fresh_parent import digest


def prepare(reference, initial_protocol, attempt):
    reference, initial_protocol, attempt = (
        p.resolve() for p in (reference, initial_protocol, attempt))
    parent = json.loads((attempt / 'parent_preparation.json').read_text())
    label = parent['label']
    native = json.loads((reference / 'native_protocol.json').read_text())
    case, = [c for c in native['cases'] if c['label'] == label]
    initial = json.loads(initial_protocol.read_text())
    inputs, = [c for c in initial['cases'] if c['label'] == label]
    destination = attempt / 'capacity'
    destination.mkdir(exist_ok=False)
    baseline = Path(inputs['native_tree'])
    candidate = attempt / 'parent/route.route_trees.csv'
    resources = Path(inputs['input_prefix'] + '.resources')
    repaired = destination / 'repaired.route_trees.csv'
    root = Path(__file__).resolve().parents[1]
    repair = root / 'tools/capacity_repair_from_baseline.py'
    commands = {'repair': [sys.executable, str(repair), str(baseline),
                           str(candidate), str(resources), str(repaired),
                           '--report', str(destination / 'repair.json')]}
    for kind, command in case['commands'].items():
        commands[kind] = [v.replace(str(reference / label), str(destination))
                          for v in command]
    preflight = {
        'candidate_tree': str(repaired), 'baseline_tree': str(baseline),
        'connections': inputs['connections'], 'resources': str(resources),
        'node_die': inputs['topology_prefix'] + '.node_die',
    }
    (destination / 'protocol.json').write_text(json.dumps(preflight, indent=2) + '\n')
    sources = [reference / 'native_protocol.json', initial_protocol, baseline,
               resources, repair, Path(__file__).resolve(),
               attempt / 'parent_preparation.json']
    sources.extend(Path(command[1]) for command in commands.values())
    result = {
        'status': 'fresh_capacity_commands_prepared_not_executed',
        'label': label, 'commands': commands,
        'source_sha256': {str(p): digest(p) for p in sources},
        'scope': 'Repair reads newly executed parent. Complete tree/native '
                 'independent audit remains required. Original parent failures '
                 'are retained; repair adds no routing sweeps.',
        'research_complete': False,
    }
    with (attempt / 'capacity_preparation.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('initial_protocol', type=Path)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    result = prepare(args.reference, args.initial_protocol, args.attempt)
    print(result['status'], result['label'], list(result['commands']))
