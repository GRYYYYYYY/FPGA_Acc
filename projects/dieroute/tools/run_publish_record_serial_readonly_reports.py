"""Archive and report the completed proposal-generation-helper routed checkpoint."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / 'work/publish_record_serial_postlink_readonly_20261018'
    preparation = directory / 'preparation.json'
    protocol = json.loads(preparation.read_text())
    for name, expected in protocol['source_sha256'].items():
        if digest(Path(name)) != expected:
            raise SystemExit('Frozen report input mismatch: ' + name)
    terminal = Path(protocol['terminal_manifest'])
    state = json.loads(terminal.read_text())
    ready = (state['status'] == protocol['required_terminal_status']
             and state.get('returncode') == protocol['required_returncode'])
    if args.check_only:
        print(json.dumps({'link_successfully_terminal': ready, 'launched': False}))
        return
    if not ready:
        raise SystemExit('Link not successfully terminal; reports not launched')
    manifest_path = directory / 'manifest.json'
    with manifest_path.open('x') as stream:
        json.dump({'status': 'archiving', 'pid': os.getpid()}, stream)
    checkpoint = Path(protocol['checkpoint'])
    checkpoint_hash = digest(checkpoint)
    archive = directory / (checkpoint_hash + '.dcp')
    image = Path(protocol['candidate']) / 'joint.xclbin'
    image_hash = digest(image)
    manifest = {'status': 'archiving', 'pid': os.getpid(),
                'checkpoint_sha256': checkpoint_hash, 'xclbin_sha256': image_hash,
                'source_sha256': {str(preparation): digest(preparation),
                                  str(terminal): digest(terminal),
                                  str(Path(__file__).resolve()): digest(Path(__file__))},
                'research_complete': False, 'board_result': False,
                'scope': protocol['scope']}
    def save():
        temporary = directory / 'manifest.tmp'
        temporary.write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.replace(manifest_path)
    try:
        with checkpoint.open('rb') as source, archive.open('xb') as target:
            shutil.copyfileobj(source, target, 8 * 1024 * 1024)
        assert digest(archive) == checkpoint_hash
        command = [str(archive) if value == 'ARCHIVED_CHECKPOINT' else value
                   for value in protocol['command_template']]
        manifest.update(status='reporting', command=command)
        save()
        with (directory / 'vivado.stdout').open('x') as log:
            child = subprocess.Popen(command, cwd=directory, stdout=log,
                                     stderr=subprocess.STDOUT)
            manifest['child_pid'] = child.pid
            save()
            result = child.wait()
        manifest['returncode'] = result
        assert result == 0, result
        assert digest(checkpoint) == digest(archive) == checkpoint_hash
        assert digest(image) == image_hash
        required = ['timing_summary.rpt', 'bus_skew.rpt', 'utilization.rpt',
                    'utilization_hierarchy.rpt', 'utilization_slr.rpt',
                    'route_status.rpt', 'drc.rpt', 'check_timing.rpt',
                    'metrics.tsv', 'clocks.tsv', 'kernel_clocks.tsv']
        reports = [directory / 'reports' / name for name in required]
        assert all(path.stat().st_size > 0 for path in reports)
        topology = directory / 'clock_freq_topology.json'
        clock_command = ['bash', str(directory / 'launch.sh'), 'xclbinutil',
                         '--input', str(image), '--dump-section',
                         'CLOCK_FREQ_TOPOLOGY:JSON:' + str(topology)]
        manifest['clock_dump_command'] = clock_command
        save()
        with (directory / 'clock_dump.log').open('x') as log:
            subprocess.run(clock_command, cwd=directory, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        json.loads(topology.read_text())
        reports.append(topology)
        assert digest(image) == image_hash
        manifest.update(status='readonly_reports_terminal_requires_interpretation',
                        checkpoint_unchanged=True,
                        report_sha256={str(path): digest(path) for path in reports})
        save()
    except BaseException as error:
        manifest.update(status='failed', error=repr(error))
        save()
        raise


if __name__ == '__main__':
    main()
