"""Copy the independently exercised initial auditor without changing checks."""
import argparse
import ast
import json
from pathlib import Path
from prepare_additional_fresh_parent import digest


def prepare(destination):
    root = Path(__file__).resolve().parents[1]
    pilot = root / 'work/additional_fresh_full_policy_integration_20261023/misex3_seed1_attempt0'
    proof_path = pilot / 'initial_v2_review/audit.json'
    proof = json.loads(proof_path.read_text())
    terminal_path = pilot / 'initial_v2_audit.terminal.json'
    terminal = json.loads(terminal_path.read_text())
    assert terminal['returncode'] == 0 and terminal['memory_guard_stop_reason'] is None
    assert proof['joint_quality_pass']
    sources = {}
    for name in ['audit_initial_case.py', 'session_sweep_auditor.py']:
        path = pilot / 'initial_auditor' / name
        assert digest(path) == proof['source_sha256'][str(path)]
        sources[str(path)] = digest(path)
    verifier = pilot / 'initial_auditor/verifier.py'
    origin = root / 'work/uniform_capacity_remaining_initial_replay_20261023/verifier.py'
    derivation = json.loads((pilot / 'initial_auditor/derivation.json').read_text())
    assert digest(verifier) == digest(origin) == derivation['source_sha256'][str(origin)]
    sources[str(verifier)] = digest(verifier)
    destination = destination.resolve()
    destination.mkdir()
    for name in ['audit_initial_case.py', 'session_sweep_auditor.py', 'verifier.py']:
        raw = (pilot / 'initial_auditor' / name).read_bytes()
        ast.parse(raw)
        (destination / name).write_bytes(raw)
    for path in [proof_path, terminal_path, origin]:
        sources[str(path)] = digest(path)
    (destination / 'preparation.json').write_text(json.dumps({
        'status': 'generic_initial_auditor_prepared_from_actual_passed_pilot',
        'checks_unchanged': True, 'files_byte_identical': True,
        'source_sha256': sources,
        'scope': 'Auditor preparation only; each new producer needs its own actual audit.',
        'research_complete': False}, indent=2) + '\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    print(prepare(parser.parse_args().destination))
