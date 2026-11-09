"""Independently validate completed 4 ns XCU280 full-color OOC evidence.

This is an internal OOC timing gate, not platform/physical-board acceptance.
Missing reports, hashes, terminal status, or timing fields fail closed.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def parse_reports(timing, route, drc):
    section = timing.split('| Design Timing Summary', 1)[1].split('| Clock Summary', 1)[0]
    rows = [line.split() for line in section.splitlines()
            if re.fullmatch(r'\s*-?\d+\.\d+(?:\s+-?\d+(?:\.\d+)?){11}\s*', line)]
    assert len(rows) == 1, 'Missing/ambiguous design timing summary'
    row = rows[0]
    clock = re.findall(r'^ap_clk\s+\{[^}]+\}\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$',
                       timing, re.M)
    assert len(clock) == 1 and float(clock[0][0]) == 4.0, 'Clock differs from 4 ns'
    counts = {}
    for name in ('no_clock', 'unconstrained_internal_endpoints', 'loops', 'latch_loops',
                 'no_input_delay', 'no_output_delay'):
        values = re.findall(r'checking ' + name + r' \((\d+)\)', timing)
        assert values and len(set(values)) == 1, 'Missing check_timing field: ' + name
        counts[name] = int(values[0])
    nets = {}
    for name in ('routable nets', 'fully routed nets', 'nets with routing errors'):
        values = re.findall(r'# of ' + name + r'\.+\s*:\s*(\d+)', route)
        assert len(values) == 1, 'Missing route field: ' + name
        nets[name] = int(values[0])
    assert 'Fully Routed' in drc, 'DRC is not from fully routed design'
    summary = drc.rsplit('1. REPORT SUMMARY\n', 1)[1].split('2. REPORT DETAILS', 1)[0]
    violations = re.search(r'Violations found:\s*(\d+)', summary)
    assert violations, 'Missing DRC summary'
    severities = {'Warning': 0, 'Critical Warning': 0, 'Error': 0}
    for line in summary.splitlines():
        fields = [field.strip() for field in line.split('|')]
        if len(fields) == 6 and fields[2] in severities and fields[4].isdigit():
            severities[fields[2]] += int(fields[4])
    assert sum(severities.values()) == int(violations.group(1)), 'Incomplete DRC rows'
    result = dict(wns_ns=float(row[0]), tns_ns=float(row[1]), setup_failing_endpoints=int(row[2]),
                  setup_total_endpoints=int(row[3]), whs_ns=float(row[4]), ths_ns=float(row[5]),
                  hold_failing_endpoints=int(row[6]), hold_total_endpoints=int(row[7]),
                  wpws_ns=float(row[8]), tpws_ns=float(row[9]), pulse_failing_endpoints=int(row[10]),
                  period_ns=4.0, check_timing=counts, routing=nets, drc=severities)
    result['internal_timing_route_drc_pass'] = bool(
        result['wns_ns'] >= 0 and result['tns_ns'] == 0 and result['setup_failing_endpoints'] == 0
        and result['setup_total_endpoints'] > 0 and result['whs_ns'] >= 0 and result['ths_ns'] == 0
        and result['hold_failing_endpoints'] == 0 and result['hold_total_endpoints'] > 0
        and result['wpws_ns'] >= 0 and result['tpws_ns'] == 0 and result['pulse_failing_endpoints'] == 0
        and all(counts[n] == 0 for n in ('no_clock', 'unconstrained_internal_endpoints', 'loops', 'latch_loops'))
        and nets['routable nets'] > 0 and nets['routable nets'] == nets['fully routed nets']
        and nets['nets with routing errors'] == 0
        and severities['Error'] == 0 and severities['Critical Warning'] == 0)
    return result


def audit(package):
    manifest = json.loads((package / 'manifest.json').read_text())
    terminal = json.loads((package / 'attempt_01_terminal.json').read_text())
    assert terminal['status'] == 'terminal' and terminal['returncode'] == 0
    assert not terminal['source_mismatches']
    assert digest(package / 'manifest.json') == terminal['manifest_sha256']
    for name, expected in manifest['files'].items():
        assert digest(package / name) == expected, name
    for name, expected in manifest['prerequisite_receipts'].items():
        assert digest(Path(name)) == expected, name
    assert digest(package / 'console.log') == terminal['console_sha256']
    required = ['synthesized.dcp', 'placed.dcp', 'routed.dcp', 'route_status.rpt',
                'timing_summary.rpt', 'utilization.rpt', 'drc.rpt']
    for name in required:
        assert name in terminal['outputs'] and digest(package / name) == terminal['outputs'][name], name
    tcl = (package / 'run.tcl').read_text()
    if manifest.get('flow') == 'route_checkpoint_recovery':
        origin = manifest['checkpoint_origin']
        original = Path(origin['package'])
        assert digest(original / 'manifest.json') == origin['manifest_sha256']
        assert digest(original / 'attempt_01_terminal.json') == origin['terminal_sha256']
        parent = json.loads((original / 'attempt_01_terminal.json').read_text())
        parent_manifest = json.loads((original / 'manifest.json').read_text())
        assert parent['status'] == 'terminal' and parent['returncode'] == 134
        assert not parent['source_mismatches']
        assert digest(original / 'console.log') == parent['console_sha256']
        assert parent['manifest_sha256'] == origin['manifest_sha256']
        assert set(origin['checkpoint_sha256']) == {'synthesized.dcp', 'placed.dcp'}
        for name, expected in parent_manifest['files'].items():
            assert digest(original / name) == expected, name
        for name, expected in origin['checkpoint_sha256'].items():
            assert parent['outputs'][name] == expected
            assert digest(original / name) == expected and digest(package / name) == expected
        assert 'open_checkpoint [file join $d placed.dcp]' in tcl
        assert tcl.index('open_checkpoint') < tcl.index('route_design')
        assert 'get_property PERIOD [get_clocks ap_clk]' in tcl
        assert not any(command in tcl for command in
                       ('create_clock', 'set_false_path', 'set_multicycle_path', 'reset_timing'))
        tcl = (original / 'run.tcl').read_text()
    else:
        assert manifest.get('flow') is None, 'Unknown implementation flow'
    assert tcl.index('read_xdc') < tcl.index('synth_design'), 'Clock must precede synthesis'
    assert 'xcu280-fsvh2892-2L-e' in tcl and '-top full_color_top' in tcl
    xdc = (package / 'clock.xdc').read_text()
    assert re.fullmatch(r'\s*create_clock -name ap_clk -period 4\.0+ \[get_ports ap_clk\]\s*', xdc)
    result = parse_reports((package / 'timing_summary.rpt').read_text(),
                           (package / 'route_status.rpt').read_text(), (package / 'drc.rpt').read_text())
    paths = []
    for block in re.split(r'(?=^Slack \()', (package / 'timing_summary.rpt').read_text(), flags=re.M):
        if 'Path Type:              Setup' not in block:
            continue
        fields = {}
        for name in ('Source', 'Destination', 'Data Path Delay', 'Logic Levels'):
            match = re.search(r'^\s*' + name + r':\s*(.+)$', block, re.M)
            assert match, 'Incomplete setup path: ' + name
            fields[name] = match.group(1).strip()
        slack = re.search(r'^Slack \((?:VIOLATED|MET)\)\s*:\s*(-?\d+\.\d+)ns', block, re.M)
        assert slack, 'Missing setup slack'
        fields['slack_ns'] = float(slack.group(1))
        paths.append(fields)
    assert paths, 'Missing detailed setup paths'
    result.update(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  actual_returncode=terminal['returncode'], frozen_files_verified=len(manifest['files']),
                  prerequisites_verified=len(manifest['prerequisite_receipts']),
                  output_hashes=terminal['outputs'], manifest_sha256=terminal['manifest_sha256'],
                  auditor_sha256=digest(Path(__file__)), reported_setup_paths=paths,
                  path_scope='Reported worst subset only, not all failing endpoints.',
                  scope='internal full-color 4ns clock-constrained routed OOC only; correctness gates separate',
                  limitations=['Input/output delays are not supplied by this OOC flow.',
                               'No platform integration or physical U280 execution is proven.'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.package.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('wns_ns', 'whs_ns', 'setup_failing_endpoints',
                                           'internal_timing_route_drc_pass')}))
    raise SystemExit(0 if result['internal_timing_route_drc_pass'] else 1)
