"""Re-extract requested/reported clock metadata; never certify board frequency."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--xclbinutil', type=Path, required=True)
    args = parser.parse_args()
    build, output, tool = args.build.resolve(), args.output.resolve(), args.xclbinutil.resolve()
    producer = build / 'manifest.json'
    manifest = json.loads(producer.read_text())
    image = build / 'joint.xclbin'
    assert manifest['inputs_unchanged'] and sha(image) == manifest['xclbin_sha256']
    output.mkdir(exist_ok=False)
    info, topology = output / 'info.txt', output / 'clock_freq_topology.json'
    commands = [[str(tool), '--input', str(image), '--info'],
                [str(tool), '--input', str(image), '--dump-section',
                 'CLOCK_FREQ_TOPOLOGY:JSON:' + str(topology)]]
    for command, log in zip(commands, [info, output / 'dump.log']):
        with log.open('w') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
    pattern = (r'Name:\s+ulp_ucs_aclk_kernel_00\s+Type:\s+SCALABLE\s+'
               r'Default Freq:\s+([\d.]+) MHz\s+Requested Freq:\s+([\d.]+) MHz\s+'
               r'Achieved Freq:\s+([\d.]+) MHz')
    match = re.search(pattern, info.read_text())
    assert match, 'Expected U280 kernel_00 clock metadata'
    default, requested, achieved = map(float, match.groups())
    assert requested == manifest['kernel_clock_mhz']
    clocks = json.loads(topology.read_text())['clock_freq_topology']
    assert int(clocks['m_count']) == len(clocks['m_clock_freq'])
    data, = [row for row in clocks['m_clock_freq'] if row['m_type'] == 'DATA']
    data_mhz = int(data['m_freq_Mhz'])
    assert 0 <= achieved - data_mhz < 1, 'Reported achieved and DATA topology need review'
    assert sha(image) == manifest['xclbin_sha256']
    files = [Path(__file__).resolve(), producer, tool, info, topology, output / 'dump.log']
    report = dict(status='hardware_clock_metadata_reextracted_and_matched_to_image',
                  requested_mhz=requested, default_mhz=default,
                  tool_reported_achieved_mhz=achieved, data_clock_topology_mhz=data_mhz,
                  reported_requested_clock_met=achieved >= requested,
                  xclbin_sha256=manifest['xclbin_sha256'], commands=commands,
                  source_sha256={str(path): sha(path) for path in files},
                  scope='Re-extracted U280 kernel_00 and DATA clock metadata tied to image hash. '
                        'No independent operating clock, adjusted-frequency timing/DRC/constraint signoff, '
                        'achievable Fmax or physical-board measurement is established.',
                  board_result=False, research_complete=False)
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k in
                      ('status', 'requested_mhz', 'tool_reported_achieved_mhz',
                       'data_clock_topology_mhz', 'reported_requested_clock_met')}))


if __name__ == '__main__':
    main()
