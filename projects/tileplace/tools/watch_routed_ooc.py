"""Wait for the original OOC terminal receipt and independently audit it once."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import time

from audit_full_color_routed_ooc import audit, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    lock = (package / 'independent_timing_watch.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (package / 'independent_timing_watch.json').exists(), 'Already watching'
    state = {'supervisor_pid': os.getpid(), 'auditor_sha256': digest(
        Path(__file__).with_name('audit_full_color_routed_ooc.py')),
        'status': 'waiting_original_implementation_terminal'}

    def save(**values):
        state.update(values, observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        tmp = package / 'independent_timing_watch.json.tmp'
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(package / 'independent_timing_watch.json')

    save()
    while not (package / 'attempt_01_terminal.json').exists():
        time.sleep(60)
        save()
    try:
        result = audit(package)
        (package / 'independent_routed_audit.json').write_text(json.dumps(result, indent=2) + '\n')
        save(status='timing_pass_awaiting_correctness_acceptance' if result['internal_timing_route_drc_pass']
             else 'timing_failed_for_primary_analysis', wns_ns=result['wns_ns'], whs_ns=result['whs_ns'],
             setup_failing_endpoints=result['setup_failing_endpoints'],
             audit_sha256=digest(package / 'independent_routed_audit.json'))
        return 0 if result['internal_timing_route_drc_pass'] else 1
    except Exception as error:
        save(status='evidence_failed_for_primary_review', error=repr(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
