"""Audit source semantic ablation, retaining anti-vacuity failures."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_counter_x_merge_ablation_v17_2026-10-09')
parent = Path('experiments/full_source_export_data_flush_counter_trace_v16_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
for name in ['design.v', 'primitives.v', 'tb.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes()
ablation = json.loads((p / 'source_ablation.json').read_text())
source = (parent / 'reference.v').read_text()
assert hashlib.sha256((parent / 'reference.v').read_bytes()).hexdigest() == ablation['parent_reference_sha256']
for old, new in ablation['replacements']:
    assert source.count(old) == 1
    source = source.replace(old, new)
assert source == (p / 'reference.v').read_text()
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages[:2])
log = (p / 'control.log').read_text()
coverage = re.findall(r'IBUS_COVERAGE requests=\s*(\d+) responses=\s*(\d+) outstanding=\s*(\d+)', log)
assert len(coverage) == 1
requests, responses, outstanding = map(int, coverage[0])
assert responses + outstanding == requests * 8
vacuous = requests == 0 or responses < 8
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
if vacuous:
    assert 'vacuous instruction transaction test' in log and not done
else:
    assert len(done) == 1 and 'Fatal' not in log and stages[2]['exit_code'] == 0
counter = re.findall(r'COUNTER_CONTROL cycle=\s*(\d+) src_singleLine=([01xz]) src_instruction=([0-9a-fxz]+) src_hold=([01xz]) src_start=([01xz]) exp_highD=([01xz]) exp_zeroInstruction=([01xz]) exp_Dinputs=([01xz]{5})', log)
assert [int(row[0]) for row in counter] == list(range(141))
result = {'bindings': protocol['bindings'], 'evidence_sha256': {name: hashlib.sha256((p / name).read_bytes()).hexdigest() for name in ['control.log', 'stages.json', 'source_ablation.json']},
          'stages': stages, 'requests': requests, 'responses': responses, 'outstanding': outstanding,
          'anti_vacuity_passed': not vacuous, 'mismatches': int(done[0]) if done else None,
          'counter_controls': counter, 'functional_admission': False,
          'scope': 'Two exact source conditional replacements only. Same adaptive driver code; realized bus input trace may differ because responses follow changed reference requests. Not a fixed-input causal ablation or original-source equivalence.'}
(p / 'ablation_audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['stages', 'requests', 'responses', 'outstanding', 'anti_vacuity_passed', 'mismatches', 'scope']}, indent=2))
