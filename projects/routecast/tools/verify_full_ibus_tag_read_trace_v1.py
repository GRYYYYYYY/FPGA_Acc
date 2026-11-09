"""Authenticate observation evidence; successful audit does not imply equality."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_ibus_tag_read_trace_v10_2026-10-09')
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
assert [int(r['cycle']) for r in rows] == list(range(125, 141))
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
parent = Path('experiments/full_source_export_ibus_tag_trace_v9_2026-10-09')
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes(), name
audit = {'bindings': protocol['bindings'], 'log_sha256': hashlib.sha256((p / 'control.log').read_bytes()).hexdigest(),
         'stages': stages, 'observations': rows, 'mismatches': int(done[0]),
         'functional_admission': False,
         'scope': 'Observation-only diagnostic. A verified execution or zero differences does not prove universal Full equivalence or physical initialization.'}
(p / 'tag_read_trace_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({'observations': rows, 'mismatches': int(done[0])}, indent=2))
