"""Rebind original parent review commands to a newly prepared routing attempt."""
import argparse
import json
from pathlib import Path
from prepare_additional_fresh_parent import digest


def prepare(review_protocol, frozen_parents, attempt):
    review_protocol = review_protocol.resolve()
    frozen_parents, attempt = frozen_parents.resolve(), attempt.resolve()
    preparation = json.loads((attempt / 'parent_preparation.json').read_text())
    for name, expected in preparation['source_sha256'].items():
        if digest(name) != expected:
            raise ValueError('Prepared source changed: ' + name)
    original = json.loads(review_protocol.read_text())
    matches = [c for c in original['cases'] if c['label'] == preparation['label']]
    if len(matches) != 1:
        raise ValueError('Expected one original case review')
    case = matches[0]
    old_parent = case['parent']
    old_recipe = str(frozen_parents / 'recipes' / preparation['label'] / 'pair.json')
    steps, sources = [], {}
    for step in case['steps']:
        command = [arg.replace(old_parent, str(attempt / 'parent'))
                   .replace(old_recipe, str(attempt / 'recipe/pair.json'))
                   for arg in step['command']]
        tool = Path(command[1])
        sources[str(tool)] = digest(tool)
        steps.append({'kind': step['kind'], 'command': command})
    if [s['kind'] for s in steps] != ['tree', 'provenance', 'writeback', 'native']:
        raise ValueError('Original review sequence changed')
    sources.update({str(review_protocol): digest(review_protocol),
                    str(attempt / 'parent_preparation.json'):
                    digest(attempt / 'parent_preparation.json'),
                    str(Path(__file__).resolve()): digest(__file__)})
    result = {'status': 'fresh_parent_review_prepared_not_executed',
              'label': preparation['label'], 'steps': steps,
              'source_sha256': sources,
              'scope': 'Original parent checks unchanged. Retain each failed check; '
                       'capacity repair and its separate full native audit remain '
                       'required before refinement. No parent quality assumed.',
              'research_complete': False}
    with (attempt / 'parent_review_protocol.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('review_protocol', type=Path)
    parser.add_argument('frozen_parents', type=Path)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    result = prepare(args.review_protocol, args.frozen_parents, args.attempt)
    print(result['status'], result['label'], len(result['steps']))
