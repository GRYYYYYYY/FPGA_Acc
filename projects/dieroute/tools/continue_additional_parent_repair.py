"""Continue a fresh exit0/exit3 parent through retained reviews and repair."""
import argparse
from pathlib import Path
import sys
import time
import traceback
from prepare_additional_fresh_parent import digest
from continue_additional_fresh_attempt import read, write, live, phase, guarded


def main(attempt):
    attempt = attempt.resolve()
    root = Path(__file__).resolve().parents[1]
    files = [root / 'tools/review_additional_parent_for_repair.py',
             root / 'tools/audit_additional_parent_session.py',
             root / 'tools/classify_parent_capacity_overuse.py',
             root / 'tools/audit_additional_fresh_capacity.py',
             attempt / 'parent_review_protocol.json',
             attempt / 'capacity/native_protocol.json']
    bound = {str(path): digest(path) for path in files}
    write(attempt / 'repair_continuation_protocol.json',
          {'source_sha256': bound, 'research_complete': False})
    owner = read(attempt / 'guard_launch.json')
    while live(owner):
        time.sleep(15)
    assert not (attempt / 'native_failure.json').exists()
    terminal = read(attempt / 'parent_execution/fresh_parent.terminal.json')
    assert terminal['returncode'] in (0, 3)
    assert terminal['memory_guard_stop_reason'] is None
    raw = read(attempt / 'parent/router_process_terminal.json')
    assert raw['returncode'] == terminal['returncode']
    for name, expected in bound.items():
        assert digest(name) == expected, name
    phase(attempt, 'raw_parent_review_guard',
          [sys.executable, str(root / 'tools/review_additional_parent_for_repair.py'), str(attempt)])
    eligibility = read(attempt / 'parent_repair_eligibility.json')
    assert eligibility['repair_eligible'] is True
    guarded(attempt / 'capacity')
    receipt = phase(attempt, 'capacity_review_guard',
                    [sys.executable, str(root / 'tools/audit_additional_fresh_capacity.py'), str(attempt)])
    write(attempt / 'capacity_audit.terminal.json', receipt)
    report = read(attempt / 'independent_native_review.json')
    write(attempt / 'parent_repair_continuation_terminal.json', {
        'status': 'fresh_parent_failure_retained_repaired_capacity_independently_reviewed',
        'raw_parent_returncode': raw['returncode'],
        'repaired_joint_quality_pass': report['rows'][0]['joint_quality_pass'],
        'scope': 'Fresh parent and repair stages only; remaining policy stages and '
                 'full attempt audit still required. Raw exit3 remains failed.',
        'research_complete': False,
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    try:
        main(args.attempt)
    except BaseException:
        write(args.attempt / 'repair_continuation_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
