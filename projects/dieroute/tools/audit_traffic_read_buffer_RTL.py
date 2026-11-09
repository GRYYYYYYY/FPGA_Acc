"""Check the isolated traffic-buffer RTL screen after its producer terminates."""
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    candidate = ROOT / 'work/lean_start_traffic_read_buffer_RTL_20261017'
    reference = ROOT / 'work/lean_start_traffic_read_buffer_HLS_20261017'
    sources = {}

    def sha(path):
        value = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        sources[str(path)] = value
        return value

    state = json.loads((candidate / 'manifest.json').read_text())
    assert state['status'] == 'RTL_terminal_requires_independent_review'
    assert state['returncode'] == 0
    protocol = json.loads((candidate / 'protocol.json').read_text())
    for filename, expected in protocol['source_sha256'].items():
        assert sha(filename) == expected, filename
    for path in (candidate / 'source').iterdir():
        if path.is_file():
            assert path.read_bytes() == (reference / 'source' / path.name).read_bytes()
    top = 'dieroute_net_commit_sharded_hbm'
    solution = candidate / 'project/solution1'
    log = (candidate / 'console.log').read_text()
    assert 'C/RTL co-simulation finished: PASS' in log
    assert 'SHARDED_DIFFERENTIAL calls=75' in log
    progress = re.findall(r'RTL Simulation : (\d+) / (\d+)', log)
    assert progress[-1] == ('75', '75')
    cosim = solution / 'sim/report' / (top + '_cosim.rpt')
    assert re.search(r'\|\s*Verilog\s*\|\s*Pass\s*\|', cosim.read_text())
    xml = solution / 'syn/report' / (top + '_csynth.xml')
    estimate = Decimal(ET.parse(xml).findtext('.//EstimatedClockPeriod'))
    constraint = solution / '.autopilot/db' / (top + '.constraint.tcl')
    block = re.search(r'set clock_constraint\s*\{(.*?)\}', constraint.read_text(), re.S)[1]
    period = Decimal(re.search(r'\bperiod\s+([0-9.]+)', block)[1])
    uncertainty = Decimal(re.search(r'\buncertainty\s+([0-9.]+)', block)[1])
    assert (period, uncertainty) == (Decimal('3.333'), Decimal('0.89991'))
    assert estimate <= period - uncertainty
    rtl = solution / 'syn/verilog' / (top + '.v')
    parent_rtl = reference / 'project/solution1/syn/verilog' / (top + '.v')
    # The exact generated top binds this simulation to the reviewed HLS adapter.
    assert rtl.read_bytes() == parent_rtl.read_bytes()
    adapter = re.search(r'dieroute_net_commit_sharded_hbm_traffic_m_axi #\((.*?)\ntraffic_m_axi_U\(', rtl.read_text(), re.S)[1]
    assert re.search(r'\.MAX_READ_BURST_LENGTH\(\s*2\s*\)', adapter)
    assert re.search(r'\.NUM_READ_OUTSTANDING\(\s*1\s*\)', adapter)
    for path in [xml, constraint, rtl, parent_rtl, cosim, candidate / 'console.log',
                 candidate / 'protocol.json', candidate / 'manifest.json', Path(__file__).resolve()]:
        sha(path)
    report = dict(status='traffic_read_buffer75_Verilog_calls_and_numeric_constraints_verified',
                  RTL_calls=75, estimated_ns=str(estimate), effective_budget_ns=str(period - uncertainty),
                  source_sha256=sources, adopted=False, research_complete=False,
                  scope='Same source and generated top as reviewed HLS screen; original75call fixture. '
                        'No full native XRT, physical timing closure or throughput claim.')
    with (candidate / 'independent_audit.json').open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(report['status'])


if __name__ == '__main__':
    main()
