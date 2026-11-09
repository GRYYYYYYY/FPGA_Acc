"""Authenticate observation evidence; successful audit does not imply equality."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_ibus_flush_control_trace_v12_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
assert 'Fatal' not in log
rx = (r'TAG_READ cycle=\s*(\d+) src_re=([01xz]) src_tagread=([01xz]) '
      r'src_fetchstuck=([01xz]) exp_re=([01xz]) exp_er=([01xz]) '
      r'exp_tagread=([01xz]) exp_held=([01xz]) exp_hit=([01xz]) '
      r'exp_fwd=([01xz]) exp_tagD=([01xz])')
keys = ['cycle', 'src_re', 'src_tagread', 'src_fetchstuck', 'exp_re', 'exp_er',
        'exp_tagread', 'exp_held', 'exp_hit', 'exp_fwd', 'exp_tagD']
rows = [dict(zip(keys, match)) for match in re.findall(rx, log)]
assert [int(r['cycle']) for r in rows] == list(range(141))
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
parent = Path('experiments/full_source_export_ibus_read_enable_trace_v11_2026-10-09')
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes(), name
control_rx = (r'READ_CONTROL cycle=\s*(\d+) exp_inputs=([01xz]{5}) '
              r'src_decode=([01xz]) src_error=([01xz]) src_fill=([01xz]) '
              r'src_flushPending=([01xz]) src_flushCounter=([0-9a-fxz]+) exp_raw=([01xz])')
control_keys = ['cycle', 'exp_inputs', 'src_decode', 'src_error', 'src_fill',
                'src_flushPending', 'src_flushCounter', 'exp_raw']
controls = [dict(zip(control_keys, match)) for match in re.findall(control_rx, log)]
assert [int(r['cycle']) for r in controls] == list(range(141))
actual_mask = re.search(r'LUT_K #\(\s*\.K\(5\),\s*\.LUT_MASK\(32\x27b([01]{32})\)\s*\) \\lut_b2692\s', (p / 'design.v').read_text())
assert actual_mask
assert actual_mask[1] == '00000100000000000000110000000000'
mask = int(actual_mask[1], 2)
for control, row in zip(controls, rows):
    pins = control['exp_inputs']
    possible = [(mask >> address) & 1 for address in range(32)
                if all(value in 'xz' or int(value) == ((address >> i) & 1)
                       for i, value in enumerate(pins))]
    predicted = str(possible[0]) if len(set(possible)) == 1 else 'x'
    assert predicted == row['exp_re'], (control, row, predicted)
    control['compatible_binary_outputs'] = sorted(set(possible))
    control['predicted_RE'] = predicted
flush_rx = (r'FLUSH_CONTROL cycle=\s*(\d+) exp_inputs=([01xz]{5}) src_halt=([01xz]) '
            r'src_flushPending=([01xz]) src_flushCounter=([0-9a-fxz]+) src_loaderValid=([01xz])')
flush_keys = ['cycle', 'exp_inputs', 'src_halt', 'src_flushPending', 'src_flushCounter', 'src_loaderValid']
flush_rows = [dict(zip(flush_keys, match)) for match in re.findall(flush_rx, log)]
assert [int(r['cycle']) for r in flush_rows] == list(range(141))
mapping = json.loads((p / 'flush_control_pin_mapping.json').read_text())
assert mapping['design_sha256'] == hashlib.sha256((p / 'design.v').read_bytes()).hexdigest()
flush_mask = int(mapping['mask'], 2)
for flush, control in zip(flush_rows, controls):
    possible = [(flush_mask >> address) & 1 for address in range(32)
                if all(value in 'xz' or int(value) == ((address >> i) & 1)
                       for i, value in enumerate(flush['exp_inputs']))]
    predicted = str(possible[0]) if len(set(possible)) == 1 else 'x'
    assert predicted == control['exp_inputs'][1]
    flush['compatible_binary_outputs'] = sorted(set(possible))
    flush['predicted_6085'] = predicted
first = next((r['cycle'] for r in rows if r['src_re'] != r['exp_re']), None)
audit = {'bindings': protocol['bindings'], 'log_sha256': hashlib.sha256((p / 'control.log').read_bytes()).hexdigest(),
         'stages': stages, 'observations': rows, 'controls': controls, 'flush_controls': flush_rows, 'first_observed_RE_difference': first, 'mismatches': int(done[0]),
         'functional_admission': False,
         'scope': 'Observation-only diagnostic. A verified execution or zero differences does not prove universal Full equivalence or physical initialization.'}
(p / 'flush_control_trace_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({'first_observed_RE_difference': first, 'controls_at_first_difference': next((c for c in controls if c['cycle'] == first), None), 'mismatches': int(done[0])}, indent=2))
