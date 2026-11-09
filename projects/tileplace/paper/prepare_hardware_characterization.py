#!/usr/bin/env python3
"""Extract verified baseline resources and fixture-only RTL simulation cycles."""
import datetime
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_full_color_outputs import audit as output_audit
from audit_full_color_routed_ooc import audit as routed_audit, digest


def simulation(package, count):
    terminal_path = package / 'rtl_attempt_01_terminal_audit.json'
    terminal = json.loads(terminal_path.read_text())
    assert terminal['returncode'] == 0 and terminal['functional_gate_pass']
    assert terminal['completed_transactions'] == count
    manifest = json.loads((package / 'manifest.json').read_text())
    for name, value in manifest['files'].items():
        assert digest(package / name) == value, name
    log = package / 'rtl_attempt_01.log'
    assert digest(log) == terminal['log_sha256']
    checked = output_audit(package, count, log)
    assert checked['full_expected_outputs_equal'] and len(checked['ports']) == count * 30
    sim = package / 'full_project/u280/sim'
    transaction_path = sim / 'report/verilog/result.transaction.rpt'
    rows = re.findall(r'^transaction\s+(\d+):\s+(\d+)\s+(\d+|x)\s*$',
                      transaction_path.read_text(), re.M)
    assert [int(row[0]) for row in rows] == list(range(count))
    latency = [int(row[1]) for row in rows]
    assert all(value > 0 for value in latency)
    assert rows[-1][2] == 'x' and all(row[2] != 'x' for row in rows[:-1])
    interval = [int(row[2]) for row in rows[:-1]]
    aggregate_path = sim / 'verilog/full_color_top.result.lat.rb'
    aggregate = {key: int(value) for key, value in re.findall(
        r'^\$(\w+) = "(\d+)"$', aggregate_path.read_text(), re.M)}
    expected = dict(MIN_LATENCY=min(latency), MAX_LATENCY=max(latency),
                    AVER_LATENCY=sum(latency) // count,
                    MIN_THROUGHPUT=min(interval), MAX_THROUGHPUT=max(interval),
                    AVER_THROUGHPUT=sum(interval) // (count - 1),
                    TOTAL_EXECUTE_TIME=sum(interval) + latency[-1])
    assert aggregate == expected, (aggregate, expected)
    summary_path = sim / 'report/full_color_top_cosim.rpt'
    summary = next(line for line in summary_path.read_text().splitlines()
                   if re.match(r'\|\s*Verilog\|', line))
    fields = [field.strip() for field in summary.split('|')[1:-1]]
    assert fields[1] == 'Pass'
    assert list(map(int, fields[2:])) == [expected[key] for key in
        ['MIN_LATENCY', 'AVER_LATENCY', 'MAX_LATENCY', 'MIN_THROUGHPUT',
         'AVER_THROUGHPUT', 'MAX_THROUGHPUT', 'TOTAL_EXECUTE_TIME']]
    bench_path = sim / 'verilog/full_color_top.autotb.v'
    bench = bench_path.read_text()
    assert f'parameter AUTOTB_TRANSACTION_NUM = {count};' in bench
    assert 'latency[i] = finish_timestamp[i] - start_timestamp[i];' in bench
    assert 'interval[i] = start_timestamp[i + 1] - start_timestamp[i];' in bench
    assert '`define AUTOTB_CLOCK_PERIOD_DIV2 2.00' in bench
    sources = [terminal_path, package / 'manifest.json', log, transaction_path,
               aggregate_path, summary_path, bench_path, package / 'full_tb.cpp']
    return dict(package=str(package.relative_to(ROOT)),
                transactions=count, full_typed_comparisons=len(checked['ports']),
                latency_cycles=latency, interval_cycles=interval,
                latency_min=min(latency), latency_max=max(latency),
                latency_integer_average=expected['AVER_LATENCY'],
                total_execution_cycles=expected['TOTAL_EXECUTE_TIME'],
                simulation_clock_period_ns=4.0,
                source_hashes={str(p.relative_to(ROOT)): digest(p) for p in sources})


def main():
    five = simulation(ROOT / 'work/full_color_trial_volatile_address_stage_2026-10-04', 5)
    four = simulation(ROOT / 'work/full_color_optimized_four_rtl_2026-10-04', 4)
    package = ROOT / 'work/optimized_clocked_synth_ooc_2026-10-09'
    timing = routed_audit(package)
    report = (package / 'utilization.rpt').read_text()
    resources = {}
    for name in ['CLB LUTs', 'CLB Registers', 'Block RAM Tile', 'DSPs', 'URAM']:
        # Global resource rows precede the per-SLR table. Match its integer
        # capacity column, unlike the utilization percentages in the SLR rows.
        matches = re.findall(r'^\|\s*' + re.escape(name) +
            r'\s*\|\s*([\d.]+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|', report, re.M)
        # Vivado repeats register totals in the CLB distribution section.
        # Accept exact repetitions but reject inconsistent global totals.
        assert matches and len(set(matches)) == 1, (name, matches)
        used, capacity, percent = matches[0]
        resources[name] = dict(used=float(used), capacity=int(capacity),
                               utilization_percent=float(percent))
    output = ROOT / 'paper/generated'
    output.mkdir(exist_ok=True)
    rows = [r'\begin{tabular}{lrr}', r'\toprule',
            r'Fixture suite & Min cycles & Max cycles \\', r'\midrule',
            f"Five-kind (5) & {five['latency_min']:,} & {five['latency_max']:,} " + r'\\',
            f"Fallback (4) & {four['latency_min']:,} & {four['latency_max']:,} " + r'\\',
            r'\bottomrule', r'\end{tabular}', '']
    table = output / 'baseline_fixture_cycles_table.tex'
    table.write_text('\n'.join(rows))
    metadata = dict(schema='TILEPLACE_BASELINE_CHARACTERIZATION_V1',
        observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        five=five, four=four, resources=resources, timing_wns_ns=timing['wns_ns'],
        routed_package=str(package.relative_to(ROOT)),
        utilization_report_sha256=digest(package / 'utilization.rpt'),
        routed_terminal_sha256=digest(package / 'attempt_01_terminal.json'),
        routed_manifest_sha256=digest(package / 'manifest.json'),
        generator_sha256=digest(Path(__file__)), table_sha256=digest(table),
        scope='Archival XSim fixture latency and implemented baseline resource use; '
              'newly extracted with source/output/terminal consistency checks',
        limitations=['Latency includes the generated AXI simulation model.',
                     'Fixture minima/maxima are not workload or candidate bounds.',
                     'The 4 ns simulation clock is not achieved physical timing.',
                     'No board runtime, throughput, transfer cost, power, energy or speedup.'])
    (output / 'baseline_characterization_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps({'five_latency_cycles': five['latency_cycles'],
                      'four_latency_cycles': four['latency_cycles'], 'resources': resources}))


if __name__ == '__main__':
    main()
