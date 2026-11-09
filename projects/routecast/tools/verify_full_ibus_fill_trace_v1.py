"""Authenticate observation evidence; successful audit does not imply equality."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_ibus_fill_trace_v8_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
assert 'Fatal' not in log
rx = (r'FILL_STATE cycle=\s*(\d+) src_fill=([01xz]) src_fire=([01xz]) '
      r'exp_fill=([01xz]) exp_fire=([01xz]) exp_D=([01xz]) '
      r'src_redo=([01xz]) src_refilling=([01xz])')
keys = ['cycle', 'src_fill', 'src_fire', 'exp_fill', 'exp_fire', 'exp_D',
        'src_redo', 'src_refilling']
rows = [dict(zip(keys, match)) for match in re.findall(rx, log)]
assert [int(r['cycle']) for r in rows] == list(range(125, 141))
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
parent = Path('experiments/full_source_export_ibus_state_trace_v7_2026-10-09')
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes(), name
audit = {'bindings': protocol['bindings'], 'log_sha256': hashlib.sha256((p / 'control.log').read_bytes()).hexdigest(),
         'stages': stages, 'observations': rows, 'mismatches': int(done[0]),
         'functional_admission': False,
         'scope': 'Observation-only diagnostic. A verified execution or zero differences does not prove universal Full equivalence or physical initialization.'}
(p / 'fill_trace_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({'observations': rows, 'mismatches': int(done[0])}, indent=2))
