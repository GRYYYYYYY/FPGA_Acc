"""Audit actual pipeline boundary telemetry and local LUT consensus semantics."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_data_flush_counter_trace_v16_2026-10-09')
parent = Path('experiments/full_source_export_pipeline_control_trace_v14_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes()
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
assert 'Fatal' not in log
boundaries = json.loads((Path('experiments/full_source_export_pipeline_boundary_trace_v15_2026-10-09') / 'observed_boundaries.json').read_text())
assert len(boundaries) == len(set(boundaries)) == 26
records = re.findall(r'PIPE_BOUNDARY cycle=\s*(\d+) index=(\d+) value=([01xz])', log)
assert len(records) == 141 * 26
values = {}
for cycle, index, value in records:
    key = (int(cycle), int(index))
    assert key not in values
    values[key] = value
assert set(values) == {(c, i) for c in range(141) for i in range(26)}
node_records = re.findall(r'PIPE_NODE cycle=\s*(\d+) net=(\S+) value=([01xz])', log)
assert len(node_records) == 141 * 14
node_values = {(int(c), n): v for c, n, v in node_records}
assert len(node_values) == len(node_records)
connectivity = json.loads((parent / 'pipeline_lut_connectivity.json').read_text())
assert connectivity['design_sha256'] == hashlib.sha256((p / 'design.v').read_bytes()).hexdigest()
issues = []
for cycle in range(141):
    sources = {n: values[cycle, i] for i, n in enumerate(boundaries)}
    sources.update({'\\lut_' + n + '_output_0_0': node_values[cycle, n] for n in connectivity['luts']})
    for n, lut in connectivity['luts'].items():
        tokens = [t.strip() for t in lut['input_concat'].split(',')][::-1]
        pin_sources = {r['target']: r['source'] for r in lut['connected_pins']}
        pins = [t[-1] if t in ["1'b0", "1'b1"] else sources[pin_sources[t]] for t in tokens]
        mask = int(lut['mask'], 2)
        compatible = {(mask >> address) & 1 for address in range(2 ** lut['K'])
                      if all(v in 'xz' or int(v) == ((address >> i) & 1) for i, v in enumerate(pins))}
        predicted = str(next(iter(compatible))) if len(compatible) == 1 else 'x'
        if predicted != node_values[cycle, n]:
            issues.append({'cycle': cycle, 'node': n, 'pins': pins, 'predicted': predicted, 'observed': node_values[cycle, n]})
flush = re.findall(r'DATA_FLUSH cycle=\s*(\d+) src_counter=([0-9a-fxz]+) src_wait=([01xz]) src_execute=([01xz])', log)
assert [int(r[0]) for r in flush] == list(range(141))
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
counter_rx = (r'COUNTER_CONTROL cycle=\s*(\d+) src_singleLine=([01xz]) src_instruction=([0-9a-fxz]+) '
              r'src_hold=([01xz]) src_start=([01xz]) exp_highD=([01xz]) '
              r'exp_zeroInstruction=([01xz]) exp_Dinputs=([01xz]{5})')
ck = ['cycle', 'src_singleLine', 'src_instruction', 'src_hold', 'src_start', 'exp_highD', 'exp_zeroInstruction', 'exp_Dinputs']
cr = [dict(zip(ck, row)) for row in re.findall(counter_rx, log)]
assert [int(row['cycle']) for row in cr] == list(range(141))
cm = json.loads((p / 'counter_high_pin_mapping.json').read_text())
assert cm['design_sha256'] == hashlib.sha256((p / 'design.v').read_bytes()).hexdigest()
for row in cr:
    possible = {(int(cm['mask'], 2) >> a) & 1 for a in range(32)
                if all(v in 'xz' or int(v) == ((a >> i) & 1) for i, v in enumerate(row['exp_Dinputs']))}
    predicted = str(next(iter(possible))) if len(possible) == 1 else 'x'
    assert predicted == row['exp_highD']
    row['compatible_highD_outputs'] = sorted(possible)
result = {'bindings': protocol['bindings'], 'stages': stages, 'boundary_records': len(records), 'lut_checks': 141 * 14,
          'local_lut_issues': issues, 'cycle4_boundaries': {n: values[4, i] for i, n in enumerate(boundaries)},
          'source_data_flush': flush, 'counter_controls': cr, 'mismatches': int(done[0]), 'functional_admission': False,
          'scope': 'Local diagnostic LUT consistency and trace evidence. Does not establish source-state relation or physical initialization.'}
(p / 'counter_trace_audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['boundary_records', 'lut_checks', 'local_lut_issues', 'cycle4_boundaries', 'mismatches']}, indent=2))
assert not issues
