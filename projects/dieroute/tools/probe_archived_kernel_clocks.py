"""Resolve all three CU clock pins by instance path in an unchanged routed DCP."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


TCL = r'''set checkpoint [lindex $argv 0]
set output [lindex $argv 1]
set_param general.maxThreads 2
open_checkpoint $checkpoint
set stream [open $output w]
puts $stream [join {cu cell reference pin clock period_ns} "\t"]
foreach cu {net_commit search_worker snapshot_search} {
    set instance "level0_i/ulp/$cu/inst"
    set cells [get_cells -quiet $instance]
    if {[llength $cells] != 1} { error "Expected exactly one CU instance: $instance" }
    set cell [lindex $cells 0]
    set pins [get_pins -quiet "$instance/ap_clk"]
    if {[llength $pins] != 1} { error "Expected one ap_clk pin: $instance" }
    set pin [lindex $pins 0]
    set clocks [get_clocks -quiet -of_objects $pin]
    if {[llength $clocks] != 1} { error "Expected exactly one clock on $pin; got $clocks" }
    set clk [lindex $clocks 0]
    puts $stream [join [list $cu $cell [get_property REF_NAME $cell] $pin $clk [get_property PERIOD $clk]] "\t"]
}
close $stream
close_design
exit 0
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('previous_reports', type=Path)
    p.add_argument('build', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    previous, build, output = [x.resolve() for x in (a.previous_reports, a.build, a.output)]
    manifest_path = previous / 'manifest.json'
    previous_state = json.loads(manifest_path.read_text())
    assert previous_state['status'] == 'archived_checkpoint_reports_require_finality_and_signoff_audit'
    checkpoint = Path(previous_state['checkpoint'])
    assert sha(checkpoint) == previous_state['checkpoint_sha256']
    protocol_path = build / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    override = protocol['environment_override']
    assert set(override) == {'LD_PRELOAD'}
    assert sha(override['LD_PRELOAD']) == protocol['inputs'][override['LD_PRELOAD']]
    output.mkdir(exist_ok=False)
    script, table = output / 'probe.tcl', output / 'kernel_clocks.tsv'
    script.write_text(TCL)
    state = dict(status='waiting_for_memory_headroom', pid=os.getpid(), checkpoint=str(checkpoint),
        checkpoint_sha256=sha(checkpoint), source_sha256={str(x): sha(x) for x in
        [Path(__file__).resolve(), manifest_path, protocol_path, script]}, board_result=False, research_complete=False)

    def save():
        (output / 'manifest.json').write_text(json.dumps(state, indent=2) + '\n')

    save()
    try:
        while True:
            memory = dict(row.split() for row in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())
            if int(memory['anon']) + 12 * 1024**3 < int(Path('/sys/fs/cgroup/memory.max').read_text()):
                break
            time.sleep(5)
        command = ['vivado', '-mode', 'batch', '-nolog', '-nojournal', '-notrace', '-source', str(script),
                   '-tclargs', str(checkpoint), str(table)]
        with (output / 'run.log').open('w') as log:
            child = subprocess.Popen(command, cwd=output, env=dict(os.environ, **override), stdout=log, stderr=subprocess.STDOUT)
            state.update(status='probing_archived_cu_clocks_read_only', child_pid=child.pid, command=command)
            save()
            code = child.wait()
        state['returncode'] = code
        assert code == 0, code
        assert sha(checkpoint) == state['checkpoint_sha256'], 'checkpoint changed'
        assert all(sha(name) == value for name, value in state['source_sha256'].items())
        with table.open() as stream:
            rows = list(csv.DictReader(stream, delimiter='\t'))
        assert len(rows) == 3 and {row['cu'] for row in rows} == {'net_commit', 'search_worker', 'snapshot_search'}
        for row in rows:
            assert row['cell'] == 'level0_i/ulp/' + row['cu'] + '/inst'
            assert row['pin'] == row['cell'] + '/ap_clk' and row['clock'] and float(row['period_ns']) > 0
        state.update(status='all_three_archived_cu_clock_pins_resolved', rows=rows, table_sha256=sha(table),
            scope='Read-only clock-pin mapping for all3CU instances on the same archived routed DCP. '
                  'Does not establish final-bitstream correspondence, adjusted187MHz signoff, '
                  '300MHz setup closure or physical operating frequency.')
        save()
    except BaseException as error:
        state.update(status='failed', error=repr(error))
        save()
        raise


if __name__ == '__main__':
    main()
