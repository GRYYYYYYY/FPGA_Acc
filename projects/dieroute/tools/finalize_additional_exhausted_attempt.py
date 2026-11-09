"""Wait for fresh fixed followup and run guarded final independent audit."""
import argparse
import json
from pathlib import Path
import sys
import time
import traceback
from prepare_additional_fresh_parent import digest
from continue_additional_fresh_attempt import read, write, live, phase


def main(attempt):
    attempt = attempt.resolve()
    root = Path(__file__).resolve().parents[1]
    auditor = root / 'tools/audit_additional_exhausted_attempt.py'
    bound = digest(auditor)
    write(attempt / 'final_review_wait_protocol.json',
          {'source_sha256': {str(auditor): bound}, 'research_complete': False})
    owner = read(attempt / 'exhausted_policy_launch.json')
    while live(owner):
        time.sleep(15)
    assert not (attempt / 'exhausted_policy_failure.json').exists()
    read(attempt / 'exhausted_policy_terminal.json')
    assert digest(auditor) == bound
    terminal = phase(attempt, 'final_review_guard',
                     [sys.executable, str(auditor), str(attempt), str(attempt / 'final_review')])
    reviewed = read(attempt / 'final_review/audit.json')
    parent_launch = read(attempt / 'parent_execution/fresh_parent.launch.json')
    result = {
        'status': 'one_fresh_integration_attempt_independently_reviewed',
        'joint_quality_pass': reviewed['joint_quality_pass'],
        'wirelength': reviewed['wirelength'], 'cpd_ns': reviewed['cpd_ns'],
        'final_tree_sha256': reviewed['final_tree_sha256'],
        'cold_parent_start_through_final_review_wall_ns': time.time_ns() - parent_launch['started_ns'],
        'final_review_actual_terminal': terminal,
        'source_sha256': {str(attempt / 'final_review/audit.json'):
                          digest(attempt / 'final_review/audit.json')},
        'scope': 'One integration attempt including waiting/setup/audits; not a speedup '
                 'benchmark, five-repeat result or board proof. Retain failed attempts.',
        'research_complete': False,
    }
    write(attempt / 'full_attempt_reviewed.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    try:
        main(args.attempt)
    except BaseException:
        write(args.attempt / 'final_review_wait_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
