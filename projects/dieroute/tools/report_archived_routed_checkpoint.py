"""Read-only Vivado reports from a captured checkpoint after its producer exits."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def identity(pid):
    path = Path('/proc', str(pid), 'stat')
    return path.read_text().split(')')[-1].split()[19] if path.exists() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build, archive, output = args.build.resolve(), args.archive.resolve(), args.output.resolve()
    output.mkdir(exist_ok=False)
    protocol_path = build / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    protocol_hash = sha(protocol_path)
    script = build / 'report_routed.tcl'
    assert protocol['inputs'][str(script)] == sha(script)
    shutil.copyfile(script, output / 'report.tcl')
    script_hash = sha(script)
    initial = json.loads((archive / 'manifest.json').read_text())
    archive_pid = initial['pid']
    archive_identity = identity(archive_pid)
    assert archive_identity is not None
    state = dict(status='waiting_for_checkpoint_archive_terminal_state', pid=os.getpid(),
                 archive_pid=archive_pid, archive_start_ticks=archive_identity,
                 script_sha256=script_hash, runner_sha256=sha(Path(__file__)),
                 protocol_sha256=protocol_hash, board_result=False, research_complete=False)

    def save():
        (output / 'manifest.json').write_text(json.dumps(state, indent=2) + '\n')

    save()
    try:
        while True:
            capture = json.loads((archive / 'manifest.json').read_text())
            if capture['status'] != 'watching_live_producer':
                break
            assert identity(archive_pid) == archive_identity, 'Archive producer disappeared without terminal evidence'
            time.sleep(5)
        state['archive_manifest_sha256'] = sha(archive / 'manifest.json')
        if not capture['checkpoints']:
            state['status'] = 'no_checkpoint_captured_no_reports_generated'
            save()
            return
        assert capture['status'] == 'producer_exited_copies_require_validation'
        assert len({row['source'] for row in capture['checkpoints']}) == 1, 'Multiple checkpoint identities need review'
        latest = capture['checkpoints'][-1]
        checkpoint = Path(latest['copy'])
        assert sha(checkpoint) == latest['sha256']
        producer_path = build / 'manifest.json'
        producer = json.loads(producer_path.read_text())
        assert identity(capture['producer_pid']) != capture['producer_start_ticks']
        assert producer['status'] in ('linked_requires_independent_routed_signoff',
                                      'link_failed_requires_diagnosis', 'failed')
        state.update(checkpoint=str(checkpoint), checkpoint_sha256=latest['sha256'],
                     producer_status=producer['status'], producer_manifest_sha256=sha(producer_path))
        while True:
            memory = dict(row.split() for row in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())
            if int(memory['anon']) + 12 * 1024**3 < int(Path('/sys/fs/cgroup/memory.max').read_text()):
                break
            state['status'] = 'waiting_for_report_memory_headroom'
            save()
            time.sleep(5)
        assert sha(protocol_path) == protocol_hash and sha(output / 'report.tcl') == script_hash
        override = protocol['environment_override']
        assert set(override) == {'LD_PRELOAD'}
        assert sha(override['LD_PRELOAD']) == protocol['inputs'][override['LD_PRELOAD']]
        command = ['vivado', '-mode', 'batch', '-nolog', '-nojournal', '-notrace',
                   '-source', str(output / 'report.tcl'), '-tclargs', str(checkpoint), str(output / 'reports')]
        state.update(status='reporting_archived_checkpoint', command=command)
        with (output / 'run.log').open('w') as log:
            child = subprocess.Popen(command, cwd=output, env=dict(os.environ, **override),
                                     stdout=log, stderr=subprocess.STDOUT)
            state['child_pid'] = child.pid
            save()
            rc = child.wait()
        assert rc == 0 and sha(checkpoint) == latest['sha256']
        required = ['timing_summary.rpt', 'utilization.rpt', 'utilization_hierarchy.rpt',
                    'utilization_slr.rpt', 'route_status.rpt', 'drc.rpt', 'check_timing.rpt',
                    'metrics.tsv', 'clocks.tsv', 'kernel_clocks.tsv']
        assert all((output / 'reports' / name).is_file() for name in required)
        state.update(status='archived_checkpoint_reports_require_finality_and_signoff_audit',
                     returncode=rc, report_sha256={name: sha(output / 'reports' / name) for name in required},
                     scope='Latest stable captured checkpoint opened read-only after producer exit; byte hash preserved. '
                           'Final-bitstream correspondence and timing/resource/clock/DRC/constraints remain unverified. '
                           'No implementation restart, rerouting, frequency reduction or board execution.')
        save()
    except BaseException as error:
        state.update(status='failed', error=repr(error))
        save()
        raise


if __name__ == '__main__':
    main()
