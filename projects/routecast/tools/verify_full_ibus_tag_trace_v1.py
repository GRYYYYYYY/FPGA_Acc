"""Verify frozen tag telemetry; execution completion is not functional admission."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_ibus_tag_trace_v9_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
assert 'Fatal' not in log
rx = (r'TAG_STATE cycle=\s*(\d+) src_decode=([01xz]) src_tagvalid=([01xz]) '
      r'src_tagaddr=([0-9a-fxz]+) src_physaddr=([0-9a-fxz]+) src_hit=([01xz]) '
      r'exp_fill_inputs=([01xz]{5})')
keys = ['cycle', 'src_decode', 'src_tagvalid', 'src_tagaddr', 'src_physaddr', 'src_hit', 'exp_fill_inputs']
rows = [dict(zip(keys, match)) for match in re.findall(rx, log)]
assert [int(r['cycle']) for r in rows] == list(range(125, 141))
mapping = json.loads((p / 'fill_lut_pin_mapping.json').read_text())
assert len(mapping) == 5
pin_sources = {int(m['target'].split('_')[-1]): m['source'] for m in mapping}
assert set(pin_sources) == set(range(5))
for row in rows:
    row['export_inputs_by_source'] = {pin_sources[i]: value for i, value in enumerate(row['exp_fill_inputs'])}
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
parent = Path('experiments/full_source_export_ibus_fill_trace_v8_2026-10-09')
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes(), name
audit = {'bindings': protocol['bindings'], 'evidence_sha256': {name: hashlib.sha256((p / name).read_bytes()).hexdigest() for name in ['control.log', 'stages.json', 'fill_lut_pin_mapping.json']},
         'stages': stages, 'observations': rows, 'mismatches': int(done[0]),
         'functional_admission': False, 'scope': 'Original failing trace with observation only; no universal sequential equivalence or physical initialization claim.'}
(p / 'tag_trace_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({'observations': rows, 'mismatches': int(done[0])}, indent=2))
