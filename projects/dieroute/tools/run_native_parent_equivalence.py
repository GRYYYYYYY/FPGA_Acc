"""Run one isolated candidate parent and compare every reference core artifact."""
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
    protocol = json.loads((directory / 'native_protocol.json').read_text())
    assert not (directory / 'native_manifest.json').exists()
    state = {'status': 'candidate_parent_running', 'pid': os.getpid(), 'research_complete': False}

    def sha(path):
        h = hashlib.sha256()
        with Path(path).open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        return h.hexdigest()

    def save():
        temporary = directory / 'native_manifest.tmp'
        temporary.write_text(json.dumps(state, indent=2) + '\n')
        temporary.replace(directory / 'native_manifest.json')

    def verify():
        for name, expected in protocol['source_sha256'].items():
            assert sha(name) == expected, name

    try:
        verify()
        save()
        started = time.monotonic_ns()
        with (directory / 'native_parent.log').open('x') as stream:
            child = subprocess.Popen(protocol['command'], stdout=stream, stderr=subprocess.STDOUT)
            state['child_pid'] = child.pid
            save()
            code = child.wait()
        state.update(returncode=code, command_wall_ns=time.monotonic_ns() - started)
        save()
        assert code == 0
        run, reference = Path(protocol['output']), Path(protocol['reference'])
        manifest = json.loads((run / 'manifest.json').read_text())
        assert manifest['status'] == 'online_router_completed_equivalence_audit_required'
        before = json.loads((reference / 'route.json').read_text())
        after = json.loads((run / 'route.json').read_text())
        before_ms, after_ms = before.pop('wall_ms'), after.pop('wall_ms')
        assert before == after, 'Non-timing parent report changed'
        files = sorted(p.name for p in reference.glob('route.*') if p.name != 'route.json')
        assert files == sorted(p.name for p in run.glob('route.*') if p.name != 'route.json')
        checked = []
        for name in files:
            assert sha(reference / name) == sha(run / name), name
            checked.append({'name': name, 'sha256': sha(run / name)})
        verify()
        refs = {str(p): sha(p) for p in [directory / 'native_protocol.json', run / 'manifest.json',
                                       run / 'route.json', reference / 'route.json', Path(__file__).resolve()]}
        result = {'status': 'candidate_full_native_parent_exact_core_equivalence_verified',
                  'core_artifacts': checked, 'reference_reported_wall_ms': before_ms,
                  'candidate_reported_wall_ms': after_ms, 'source_sha256': refs, 'research_complete': False,
                  'scope': 'One unchanged-input parent run after isolated source optimization. All route.* artifacts and non-timing report match reference. Single timings under background load are descriptive, not a matched repeated speedup, full-refinement rerun or FPGA result.'}
        with (directory / 'native_equivalence_audit.json').open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
        state['status'] = 'candidate_native_parent_equivalence_ready'
        save()
    except BaseException:
        state.update(status='candidate_native_parent_stopped_requires_review', error=traceback.format_exc())
        save()
        raise


if __name__ == '__main__':
    main()
