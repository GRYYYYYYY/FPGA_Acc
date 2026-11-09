"""Run a supplied fresh workflow only after authenticated original-budget preflight."""
import argparse
import json
import subprocess
import time
from pathlib import Path
from certified_budget_execution_gate_v2 import preflight
from pre_route_endpoints import sha


def execute(admission, authority, endpoints, budget, command, cwd, output):
    if not command:
        raise ValueError('A candidate workflow command is required')
    output = Path(output)
    output.mkdir(exist_ok=False)
    started = time.perf_counter()
    decision = preflight(admission, authority, endpoints, budget)
    preflight_seconds = time.perf_counter() - started
    protocol = dict(preflight=decision, command=list(command), cwd=str(Path(cwd).resolve()),
                    source_sha256=sha(Path(__file__)),
                    gate_source_sha256=sha(Path(__file__).with_name(
                        'certified_budget_execution_gate_v2.py')))
    pp = output/'protocol.json'
    pp.write_text(json.dumps(protocol, indent=2)+'\n')
    code = None
    launched = False
    if decision['run_candidate_pipeline']:
        launched = True
        with (output/'candidate.log').open('x') as log:
            code = subprocess.run(command, cwd=cwd, stdout=log,
                                  stderr=subprocess.STDOUT).returncode
    elapsed = time.perf_counter()-started
    report = dict(protocol_sha256=sha(pp), preflight_seconds=preflight_seconds,
                  workflow_entry_seconds=elapsed, candidate_launched=launched,
                  candidate_exit_code=code, decision=decision['decision'],
                  candidate_quality_accepted=False,
                  full_original_input_workflow_seconds=None,
                  scope='Strict original-budget execution entry using provided verified '
                        'floor cache. Successful subprocess exit alone never establishes '
                        'quality acceptance. Skip is model infeasibility, not routing '
                        'completion or a speedup; cache preparation cost excluded.')
    (output/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('admission', 'authority', 'endpoints', 'budget', 'cwd', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    command = a.command[1:] if a.command[:1] == ['--'] else a.command
    report = execute(a.admission, a.authority, a.endpoints, a.budget,
                     command, a.cwd, a.output)
    print(json.dumps(report, indent=2))
    if report['candidate_exit_code']:
        raise SystemExit(report['candidate_exit_code'])
