"""Compare same-ABI sharded commit XOs; HLS estimates only, no routed signoff."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        xml_name, = [n for n in archive.namelist() if n.endswith('/kernel.xml')]
        kernel = ET.fromstring(archive.read(xml_name)).find('kernel')
        assert kernel is not None
        assert kernel.attrib['name'] == 'dieroute_net_commit_sharded_hbm'
        ports = [dict(p.attrib) for p in kernel.findall('ports/port')]
        args = [dict(a.attrib) for a in kernel.findall('args/arg')]
        assert len(args) == 29
        assert sum(a['addressQualifier'] == '1' for a in args) == 17
        assert sum(p['mode'] == 'master' for p in ports) == 6
        member, = [n for n in archive.namelist() if n.endswith('/dieroute_net_commit_sharded_hbm_csynth.rpt')]
        raw = archive.read(member)
    report = raw.decode()
    clock = re.search(r'\|ap_clk\s*\|\s*([\d.]+) ns\|\s*([\d.]+) ns\|\s*([\d.]+) ns\|', report)
    assert clock
    total = re.search(r'^\|Total\s*\|([^\n]+)', report.split('== Utilization Estimates', 1)[1], re.M)
    values = [int(v.strip()) for v in total[1].split('|') if v.strip()]
    assert len(values) == 5
    return dict(xo_sha256=sha(path), ports=ports, args=args,
                control_protocol=kernel.attrib['hwControlProtocol'],
                version=re.search(r'\* Version:\s+(.+)', report)[1],
                device=re.search(r'\* Target device:\s+(\S+)', report)[1],
                target_ns=float(clock[1]), estimated_ns=float(clock[2]),
                uncertainty_ns=float(clock[3]),
                resources=dict(zip(['BRAM_18K', 'DSP', 'FF', 'LUT', 'URAM'], values)),
                report_sha256=hashlib.sha256(raw).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('parent', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    a = parser.parse_args()
    before, after = inspect(a.parent), inspect(a.candidate)
    for field in ['ports', 'args', 'control_protocol', 'version', 'device', 'target_ns', 'uncertainty_ns']:
        assert before[field] == after[field], 'incompatible comparison: ' + field
    result = dict(status='same_abi_sharded_commit_hls_estimates_compared',
                  parent=before, candidate=after,
                  resource_delta={k: after['resources'][k]-v for k,v in before['resources'].items()},
                  source_sha256={str(Path(__file__).resolve()): sha(Path(__file__))},
                  scope='XO metadata ABI equality and embedded HLS estimates only. Does not prove source equivalence, producer provenance, routed timing, latency, throughput or board operation.',
                  board_result=False, research_complete=False)
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], resource_delta=result['resource_delta'])))


if __name__ == '__main__':
    main()
