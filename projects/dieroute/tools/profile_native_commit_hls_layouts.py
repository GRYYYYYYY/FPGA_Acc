"""Compare embedded commit-kernel HLS estimates; no physical mapping benefit claim."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('unbanked', type=Path)
    parser.add_argument('banked', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    records = {}
    sources = {str(Path(__file__).resolve()): sha(Path(__file__).read_bytes())}
    for label, directory, kernel in [('unbanked', args.unbanked, 'dieroute_net_commit_hbm'),
                                     ('banked', args.banked, 'dieroute_net_commit_sharded_hbm')]:
        directory = directory.resolve()
        xo, producer = directory / 'commit.xo', directory / 'manifest.json'
        producer_bytes = producer.read_bytes()
        manifest = json.loads(producer_bytes)
        producer_snapshot = args.output / (label + '_producer_manifest.json')
        producer_snapshot.write_bytes(producer_bytes)
        digest = sha(xo.read_bytes())
        expected = (manifest['inputs'][str(xo)] if label == 'unbanked' else
                    manifest['xo_sha256']['commit'])
        assert digest == expected
        with zipfile.ZipFile(xo) as archive:
            member, = [name for name in archive.namelist() if name.endswith('/' + kernel + '_csynth.rpt')]
            data = archive.read(member)
        report = data.decode()
        assert "Vitis HLS Report for '" + kernel + "'" in report
        version = re.search(r'\* Version:\s+(.+)', report)[1]
        part = re.search(r'\* Target device:\s+(\S+)', report)[1]
        clock = re.search(r'\|ap_clk\s*\|\s*([\d.]+) ns\|\s*([\d.]+) ns\|\s*([\d.]+) ns\|', report)
        assert clock
        section = report.split('== Utilization Estimates', 1)[1]
        total = re.search(r'^\|Total\s*\|([^\n]+)', section, re.M)
        values = [int(value.strip()) for value in total[1].split('|') if value.strip()]
        assert len(values) == 5
        resources = dict(zip(('BRAM_18K', 'DSP', 'FF', 'LUT', 'URAM'), values))
        latency = report.split('+ Latency:', 1)[1].split('+ Detail:', 1)[0]
        assert re.search(r'\|\s*\?\s*\|\s*\?\s*\|', latency), 'Review changed latency evidence'
        target = args.output / (label + '_csynth.rpt')
        target.write_bytes(data)
        sources.update({str(xo): digest, str(producer_snapshot.resolve()): sha(producer_bytes),
                        str(target.resolve()): sha(data)})
        records[label] = dict(kernel=kernel, version=version, part=part,
                              clock_target_ns=float(clock[1]), clock_estimate_ns=float(clock[2]),
                              clock_uncertainty_ns=float(clock[3]), resources=resources,
                              top_latency_cycles=None, top_interval_cycles=None,
                              embedded_report_member=member, producer_original_path=str(producer))
    before, after = records['unbanked'], records['banked']
    for field in ('version', 'part', 'clock_target_ns', 'clock_uncertainty_ns'):
        assert before[field] == after[field]
    changes = {name: dict(unbanked=value, banked=after['resources'][name],
                          delta=after['resources'][name] - value,
                          delta_percent=100 * (after['resources'][name] / value - 1) if value else None)
               for name, value in before['resources'].items()}
    result = dict(status='embedded_commit_hls_layout_estimates_profiled', kernels=records,
                  resource_changes=changes, source_sha256=sources,
                  scope='Embedded top HLS reports from successful hardware XO compilations, '
                        'same reported tool/device/clock constraints. Distinct kernel layouts, '
                        'not a complete controlled mapping ablation. Top latency and interval '
                        'are unknown. HLS period estimates are not routed frequency; resource '
                        'estimates are not final placement usage, bandwidth, throughput or energy.',
                  board_result=False, research_complete=False)
    (args.output / 'profile.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], resource_changes=changes)))


if __name__ == '__main__':
    main()
