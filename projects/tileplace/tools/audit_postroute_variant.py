"""Verify a completed physical-optimization chain back to its standard OOC run.

Reads immutable inputs and real terminal receipts; never submits or retries jobs.
This proves internal timing provenance, not functional acceptance or adoption.
"""
import argparse
import datetime
import json
from pathlib import Path

from audit_full_color_routed_ooc import audit as audit_standard, digest, parse_reports


DIRECTIVES = {
    'independent_postroute_Explore_NoTimingRelaxation': 'Explore',
    'independent_postroute_AggressiveExplore_NoTimingRelaxation': 'AggressiveExplore',
}


def expected_tcl(directive):
    return '''set d [file dirname [file normalize [info script]]]
cd $d
set_param general.maxThreads 8
open_checkpoint [file join $d input_routed.dcp]
if {[get_property PART [current_design]] ne "xcu280-fsvh2892-2L-e"} {error "Unexpected part"}
if {[llength [get_clocks]] != 1 || [get_property PERIOD [get_clocks ap_clk]] != 4.0} {error "Unexpected clock"}
phys_opt_design -directive ''' + directive + '''
route_design -directive NoTimingRelaxation
if {[get_property PERIOD [get_clocks ap_clk]] != 4.0} {error "Clock changed"}
write_checkpoint -force [file join $d routed.dcp]
report_route_status -file [file join $d route_status.rpt]
report_timing_summary -delay_type min_max -max_paths 20 -file [file join $d timing_summary.rpt]
report_utilization -file [file join $d utilization.rpt]
report_drc -file [file join $d drc.rpt]
exit
'''


def audit(package, ancestors=()):
    package = package.resolve()
    if package in ancestors:
        raise ValueError('Checkpoint ancestry cycle: ' + str(package))
    manifest = json.loads((package / 'manifest.json').read_text())
    flow = manifest.get('flow', '')
    if not flow.startswith('independent_postroute_'):
        result = audit_standard(package)
        result.update(standard_route_origin=str(package), physical_variant_depth=0)
        return result
    if flow not in DIRECTIVES:
        raise ValueError('Unsupported physical flow: ' + flow)
    terminal = json.loads((package / 'attempt_01_terminal.json').read_text())
    assert terminal['status'] == 'terminal' and terminal['returncode'] == 0
    assert not terminal['source_mismatches']
    assert terminal['manifest_sha256'] == digest(package / 'manifest.json')
    assert terminal['console_sha256'] == digest(package / 'console.log')
    for name, value in manifest['files'].items():
        assert digest(package / name) == value, name
    for name, value in manifest['prerequisite_receipts'].items():
        assert digest(Path(name)) == value, name
    # Exact command sequence rules out changed clocks, exceptions and extra steps.
    assert (package / 'run.tcl').read_text() == expected_tcl(DIRECTIVES[flow])
    origin = Path(manifest['checkpoint_origin']).resolve()
    parent = audit(origin, (*ancestors, package))
    assert digest(package / 'input_routed.dcp') == parent['output_hashes']['routed.dcp']
    parent_manifest = json.loads((origin / 'manifest.json').read_text())
    if parent['physical_variant_depth']:
        assert manifest['source_package'] == parent_manifest['source_package']
    required = {'routed.dcp', 'route_status.rpt', 'timing_summary.rpt',
                'utilization.rpt', 'drc.rpt'}
    assert set(terminal['outputs']) == required
    for name, value in terminal['outputs'].items():
        assert digest(package / name) == value, name
    result = parse_reports((package / 'timing_summary.rpt').read_text(),
                           (package / 'route_status.rpt').read_text(),
                           (package / 'drc.rpt').read_text())
    result.update(
        observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        actual_returncode=terminal['returncode'],
        manifest_sha256=digest(package / 'manifest.json'),
        terminal_sha256=digest(package / 'attempt_01_terminal.json'),
        output_hashes=terminal['outputs'],
        auditor_sha256=digest(Path(__file__)),
        standard_auditor_sha256=digest(Path(__file__).with_name('audit_full_color_routed_ooc.py')),
        checkpoint_origin=str(origin),
        parent_manifest_sha256=digest(origin / 'manifest.json'),
        parent_terminal_sha256=digest(origin / 'attempt_01_terminal.json'),
        parent_wns_ns=parent['wns_ns'],
        standard_route_origin=parent['standard_route_origin'],
        physical_variant_depth=parent['physical_variant_depth'] + 1,
        frozen_files_verified=len(manifest['files']),
        prerequisites_verified=len(manifest['prerequisite_receipts']),
        scope='Internal 4 ns OOC physical provenance only; functional gates, '
              'source adoption, platform I/O timing and board execution are separate.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.package)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
                      ['wns_ns', 'tns_ns', 'physical_variant_depth',
                       'internal_timing_route_drc_pass']}))
