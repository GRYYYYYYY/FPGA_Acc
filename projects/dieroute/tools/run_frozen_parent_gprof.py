"""Profile unchanged routing source and require exact reference output equality."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback


def main():
    directory = Path(sys.argv[1]).resolve()
    protocol = json.loads((directory / 'profile_protocol.json').read_text())
    assert not (directory / 'manifest.json').exists(), 'No replay'
    state = {'status': 'running_instrumented_parent', 'pid': os.getpid(), 'steps': [], 'research_complete': False}

    def sha(path):
        h = hashlib.sha256()
        with Path(path).open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        return h.hexdigest()

    def save():
        temp = directory / 'manifest.tmp'
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(directory / 'manifest.json')

    def verify():
        for name, expected in protocol['source_sha256'].items():
            assert sha(name) == expected, name

    try:
        verify()
        save()
        environment = dict(os.environ, GMON_OUT_PREFIX=protocol['gmon_prefix'])
        with (directory / 'parent_execution.log').open('x') as stream:
            child = subprocess.Popen(protocol['command'], stdout=stream, stderr=subprocess.STDOUT, env=environment)
            state['child_pid'] = child.pid
            save()
            code = child.wait()
        state['parent_returncode'] = code
        save()
        assert code == 0
        run = Path(protocol['output'])
        manifest = json.loads((run / 'manifest.json').read_text())
        assert manifest['status'] == 'online_router_completed_equivalence_audit_required'
        gmon = Path(protocol['gmon_prefix'] + '.' + str(manifest['pid']))
        assert gmon.is_file() and gmon.stat().st_size > 0
        for name, flags in [('flat_profile.txt', ['-p']), ('call_graph.txt', [])]:
            with (directory / name).open('x') as stream:
                subprocess.run(['gprof', '-b', *flags, protocol['binary'], str(gmon)],
                               stdout=stream, stderr=subprocess.STDOUT, check=True)
        state['status'] = 'checking_profiled_output_equivalence'
        save()
        reference = Path(protocol['reference'])
        before = json.loads((reference / 'route.json').read_text())
        after = json.loads((run / 'route.json').read_text())
        before.pop('wall_ms')
        after.pop('wall_ms')
        assert before == after, 'Non-timing routing report changed'
        files = sorted(p.name for p in reference.glob('route.*') if p.name != 'route.json')
        assert files and files == sorted(p.name for p in run.glob('route.*') if p.name != 'route.json')
        checked = []
        for name in files:
            assert sha(reference / name) == sha(run / name), name
            checked.append({'name': name, 'sha256': sha(run / name)})
        verify()
        result = {'status': 'instrumented_parent_exact_core_artifacts_and_report_equivalent',
                  'core_artifacts': checked, 'gmon': str(gmon),
                  'source_sha256': {str(p): sha(p) for p in [directory / 'profile_protocol.json',
                                                           run / 'manifest.json', run / 'route.json',
                                                           reference / 'route.json', gmon,
                                                           directory / 'flat_profile.txt', directory / 'call_graph.txt']},
                  'scope': 'One instrumented CPU parent repetition. Exact non-timing report and all route.* artifacts match reference. Gprof samples/call accounting include instrumentation overhead; not a speedup measurement, five-repeat protocol, QoR generalization or board result.',
                  'research_complete': False}
        with (directory / 'equivalence_audit.json').open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        state['status'] = 'profile_and_exact_output_equivalence_ready'
        save()
    except BaseException:
        state.update(status='profile_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
