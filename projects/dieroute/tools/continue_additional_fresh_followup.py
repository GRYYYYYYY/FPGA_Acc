"""Queue original fixed followup after one fresh attempt's initial audit."""
from pathlib import Path
import argparse
import json
import sys
import time
import traceback
from prepare_additional_fresh_parent import digest
from continue_additional_fresh_attempt import read, write, live, guarded


def main(attempt):
    attempt = attempt.resolve()
    root = Path(__file__).resolve().parents[1]
    template = root / 'work/uniform_capacity_seq3_followup_20261023'
    bound = {str(template / name): digest(template / name)
             for name in ['run.py', 'protocol.json', 'guarded_execution.py']}
    write(attempt / 'fresh_followup_wait_protocol.json',
          {'source_sha256': bound, 'research_complete': False})
    owner = read(attempt / 'continuation_launch.json')
    while live(owner):
        time.sleep(15)
    assert not (attempt / 'continuation_failure.json').exists()
    assert read(attempt / 'initial_audit.terminal.json')['returncode'] == 0
    for name, expected in bound.items():
        assert digest(name) == expected, name
    report = read(attempt / 'initial_review/audit.json')
    label = read(attempt / 'parent_preparation.json')['label']
    assert report['label'] == label
    directory = attempt / 'fixed_followup'
    directory.mkdir()
    (directory / 'execution').mkdir()
    script = (template / 'run.py').read_text()
    old = "initial['label'] == 'seq_seed3'"
    assert script.count(old) == 1
    script = script.replace(old, "initial['label'] == " + repr(label))
    assert script.count('R = D.parents[1]') == 1
    script = script.replace('R = D.parents[1]', 'R = Path(' + repr(str(root)) + ')')
    (directory / 'run.py').write_text(script)
    (directory / 'guarded_execution.py').write_bytes((template / 'guarded_execution.py').read_bytes())
    protocol = read(template / 'protocol.json')
    sources = dict(protocol['source_sha256'])
    del sources[protocol['case_protocol']]
    del sources[str(template / 'run.py')]
    protocol.update(initial_terminal=str(attempt / 'initial_audit.terminal.json'),
                    initial_report=str(attempt / 'initial_review/audit.json'),
                    case_protocol=str(attempt / 'initial' / label / 'protocol.json'),
                    scope='Original fixed followup for one fresh integration attempt. '
                          'Not five complete independent executions or board proof.')
    for name in [protocol['case_protocol'], str(directory / 'run.py')]:
        sources[name] = digest(name)
    for name, expected in sources.items():
        assert digest(name) == expected, name
    protocol['source_sha256'] = sources
    write(directory / 'protocol.json', protocol)
    sources = dict(sources)
    for path in [directory / 'protocol.json', directory / 'guarded_execution.py']:
        sources[str(path)] = digest(path)
    write(directory / 'native_protocol.json',
          {'cases': [{'label': 'execution', 'commands': {
              'followup': [sys.executable, str(directory / 'run.py')]}}],
           'source_sha256': sources, 'research_complete': False})
    guarded(directory)
    final = read(directory / 'manifest.json')
    write(attempt / 'fresh_followup_terminal.json',
          {'status': 'fresh_fixed_followup_terminal_final_full_attempt_audit_required',
           'final_report': final['final_report'], 'research_complete': False})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('attempt', type=Path)
    args = parser.parse_args()
    try:
        main(args.attempt)
    except BaseException:
        write(args.attempt / 'fresh_followup_failure.json',
              {'error': traceback.format_exc(), 'research_complete': False})
        raise
