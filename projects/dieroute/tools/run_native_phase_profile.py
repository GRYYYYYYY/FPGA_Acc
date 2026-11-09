"""Interpret phase timers only after complete native output equivalence."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'native_protocol.json').read_text())
    root = Path(__file__).resolve().parents[1]
    with (directory / 'equivalence_supervisor.log').open('x') as stream:
        subprocess.run([sys.executable, str(root / 'tools/run_native_parent_equivalence.py'), str(directory)],
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    audit = directory / 'native_equivalence_audit.json'
    equivalent = json.loads(audit.read_text())
    assert equivalent['status'] == 'candidate_full_native_parent_exact_core_equivalence_verified'
    log = Path(protocol['output']) / 'routing.log'
    lines = [v for v in log.read_text().splitlines() if v.startswith('DIEROUTE_PHASE_PROFILE ')]
    assert len(lines) == 1
    data = json.loads(lines[0].split(' ', 1)[1])
    assert data['clock_errors'] == 0
    phases = data['phases']
    total = phases['execute_total']['cpu_ns']
    assert total > 0 and phases['execute_total']['calls'] > 0
    child_total = sum(v['cpu_ns'] for k, v in phases.items() if k != 'execute_total')
    assert child_total <= total
    for value in phases.values():
        value['fraction_of_execute_thread_cpu'] = value['cpu_ns'] / total
    paths = [audit, log, directory / 'native_protocol.json', directory / 'build_audit.json', Path(__file__).resolve()]
    result = {'status': 'equivalent_native_parent_phase_cpu_and_wall_profile_ready', 'phases': phases,
              'other_execute_thread_cpu_ns': total - child_total,
              'source_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              'scope': 'One six-scope instrumented parent with exact native core output equality. Execute contains other five nonoverlapping scopes; thread CPU excludes descheduling, wall includes it. Timer overhead remains; identifies this run phase costs, not matched speedup, generalization, full-refinement cost or FPGA performance.',
              'research_complete': False}
    with (directory / 'phase_profile_audit.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['status'])


if __name__ == '__main__':
    main()
