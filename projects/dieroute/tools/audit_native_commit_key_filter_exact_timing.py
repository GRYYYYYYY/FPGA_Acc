"""Supplement frozen functional review with exact generated HLS clock constraints."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'work/native_commit_key_filter_HLS_20261015'


def main():
    refs = {}

    def bind(path):
        refs[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()

    receipt = RUN / 'independent_audit.json'
    functional = json.loads(receipt.read_text())
    assert functional['status'] == 'enabled_key_filter120_Verilog_calls_external_ABI_reviewed'
    for path, expected in functional['source_sha256'].items():
        p = Path(path)
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected, path
    rows = []
    for suite in ('small', 'large'):
        solution = RUN / suite / 'project/solution1'
        constraint = solution / '.autopilot/db/dieroute_net_commit_sharded_hbm.constraint.tcl'
        xml = solution / 'syn/report/dieroute_net_commit_sharded_hbm_csynth.xml'
        text = constraint.read_text()
        block = re.search(r'set clock_constraint\s*\{(.*?)\}', text, re.S)
        assert block, constraint
        def number(key):
            values = re.findall(r'\b' + key + r'\s+([0-9.]+)', block.group(1))
            assert len(values) == 1, (key, values)
            return Decimal(values[0])
        period, uncertainty = number('period'), number('uncertainty')
        estimate = Decimal(ET.parse(xml).findtext('.//EstimatedClockPeriod'))
        budget = period - uncertainty
        assert period == Decimal('3.333') and uncertainty == Decimal('0.89991')
        log = RUN / suite / 'console.log'
        rows.append(dict(suite=suite, requested_ns=str(period), uncertainty_ns=str(uncertainty),
                         effective_budget_ns=str(budget), estimated_ns=str(estimate),
                         excess_ns=str(estimate-budget), reported_estimate_pass=estimate <= budget,
                         warning_emitted='HLS 200-871' in log.read_text()))
        for path in (constraint, xml, log):
            bind(path)
    for path in (receipt, RUN/'manifest.json', Path(__file__).resolve()):
        bind(path)
    report = dict(status='functional120_pass_numeric_effective_timing_failed'
                  if not all(r['reported_estimate_pass'] for r in rows)
                  else 'functional120_pass_reported_estimate_within_effective_budget',
                  suites=rows, source_sha256=refs, adopted=False, board_result=False,
                  research_complete=False,
                  scope='Compare final synthesis estimates to exact generated period minus uncertainty. '
                        'Warnings are independent observations. No routed or physical timing proof.')
    with (RUN/'exact_timing_audit.json').open('x') as out:
        json.dump(report, out, indent=2)
        out.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'source_sha256'}))


if __name__ == '__main__':
    main()
