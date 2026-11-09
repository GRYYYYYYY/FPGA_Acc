"""Prepare fresh parent, retained reviews, capacity and initial stages; no execution."""
import argparse
import json
from pathlib import Path
from prepare_additional_fresh_parent import prepare as parent_prepare, digest
from prepare_additional_parent_review import prepare as review_prepare
from prepare_additional_fresh_capacity import prepare as capacity_prepare
from prepare_additional_initial_stage import prepare as initial_prepare
from prepare_additional_initial_auditor import prepare as auditor_prepare


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare(label, attempt):
    root = Path(__file__).resolve().parents[1]
    work = root / 'work'
    frozen = work / 'additional_circuit_frozen_parents_20261020'
    initial_source = work / 'uniform_capacity_initial_refinement9_20261023/protocol.json'
    original = json.loads(initial_source.read_text())
    assert sum(c['label'] == label for c in original['cases']) == 1
    attempt = attempt.resolve()
    parent = parent_prepare(frozen, label, attempt)
    parent['original_command'] = parent['command'][:]
    runner = root / 'tools/run_additional_parent_failure_preserving.py'
    parent['command'][1] = str(runner)
    parent['source_sha256'][str(runner)] = digest(runner)
    parent['scope'] = 'Fresh recipe; raw router exit0 or3 retained, actual normal timing STOP required. No execution yet.'
    write(attempt / 'parent_preparation.json', parent)
    review = review_prepare(work / 'additional_circuit_parent_reviews_v2_20261020/protocol.json', frozen, attempt)
    session_auditor = root / 'tools/audit_additional_parent_session.py'
    provenance, = [s for s in review['steps'] if s['kind'] == 'provenance']
    provenance['command'][1] = str(session_auditor)
    review['source_sha256'][str(session_auditor)] = digest(session_auditor)
    write(attempt / 'parent_review_protocol.json', review)
    cap = capacity_prepare(work / 'uniform_parent_capacity_native9_20261023', initial_source, attempt)
    template = work / 'uniform_capacity_seq3_followup_20261023/guarded_execution.py'
    raw_guard = template.read_text()
    assert raw_guard.count('R=D.parents[1]') == 1
    guard = raw_guard.replace('R=D.parents[1]', 'R=Path(' + repr(str(root)) + ')')
    (attempt / 'guarded_execution.py').write_text(guard)
    (attempt / 'parent_execution').mkdir()
    sources = dict(parent['source_sha256'])
    for p in [attempt / 'parent_preparation.json', attempt / 'recipe/pair.json', attempt / 'guarded_execution.py']:
        sources[str(p)] = digest(p)
    write(attempt / 'native_protocol.json', {
        'cases': [{'label': 'parent_execution', 'commands': {'fresh_parent': parent['command']}}],
        'source_sha256': sources, 'research_complete': False})
    directory = attempt / 'capacity'
    (directory / 'execution').mkdir()
    (directory / 'guarded_execution.py').write_text(guard)
    sources = dict(cap['source_sha256'])
    vpr = Path(original['validation_vpr'])
    sources[str(vpr)] = digest(vpr)
    for p in [directory / 'guarded_execution.py', directory / 'protocol.json', attempt / 'capacity_preparation.json']:
        sources[str(p)] = digest(p)
    write(directory / 'native_protocol.json', {
        'cases': [{'label': 'execution', 'commands': cap['commands']}],
        'source_sha256': sources, 'research_complete': False})
    initial_prepare(attempt, attempt / 'initial')
    auditor_prepare(attempt / 'initial_auditor')
    write(attempt / 'full_preparation.json', {
        'status': 'generic_full_stage_preparation_not_executed', 'label': label,
        'source_sha256': {str(p): digest(p) for p in
            [attempt / 'native_protocol.json', attempt / 'parent_review_protocol.json',
             directory / 'native_protocol.json', attempt / 'initial/protocol.json',
             attempt / 'initial_auditor/preparation.json', Path(__file__).resolve()]},
        'next': 'Generic driver must execute raw parent, eligibility, repair and audits, then branch by actual parent iterations; final independent audit required.',
        'research_complete': False})
    return attempt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    print(prepare(args.label, args.attempt))
