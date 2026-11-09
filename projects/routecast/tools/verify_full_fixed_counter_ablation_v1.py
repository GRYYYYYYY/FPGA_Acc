"""Authenticate fixed-input source ablation; no original-source admission."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_fixed_counter_ablation_v20_2026-10-09')
base = Path('experiments/full_source_export_fixed_bus_replay_v19_2026-10-09')
ab = Path('experiments/full_source_export_counter_x_merge_ablation_v17_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
for name in ['design.v', 'primitives.v', 'tb.v', 'control.py', 'run.py', 'frozen_bus_trace.json']:
    assert (p / name).read_bytes() == (base / name).read_bytes()
assert hashlib.sha256((base / 'fixed_replay_audit.json').read_bytes()).hexdigest() == protocol['baseline_replay_audit_sha256']
assert json.loads((base / 'fixed_replay_audit.json').read_text())['replay_fidelity_on_captured_records']
assert hashlib.sha256((ab / 'source_ablation.json').read_bytes()).hexdigest() == protocol['source_ablation_manifest_sha256']
source = (base / 'reference.v').read_text()
for old, new in json.loads((ab / 'source_ablation.json').read_text())['replacements']:
    assert source.count(old) == 1
    source = source.replace(old, new)
assert source == (p / 'reference.v').read_text()
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
base_log = (base / 'control.log').read_text()
assert 'Fatal' not in log
rx = (r'BUS_INPUT cycle=\s*(\d+) reset=([01]) debugReset=([01]) ready=([01]) '
      r'rsp_valid=([01]) rsp_data=([0-9a-fA-F]+) rsp_error=([01])')
actual = re.findall(rx, log)
expected = re.findall(rx, base_log)
assert actual == expected and [int(r[0]) for r in actual] == list(range(512))
coverage = re.findall(r'IBUS_COVERAGE requests=\s*(\d+) responses=\s*(\d+) outstanding=\s*(\d+)', log)
assert len(coverage) == 1
requests, responses, outstanding = map(int, coverage[0])
assert requests > 0 and responses >= 8 and responses + outstanding == 8 * requests
def records(text, prefix):
    return re.findall(r'@"(' + prefix + r'[^\n]*?)\\n"', text)
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
bdone = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', base_log)
assert len(done) == len(bdone) == 1
changes = {}
for prefix in ['COUNTER_CONTROL', 'PIPE_BOUNDARY', 'DATA_FLUSH', 'PIPE_NODE', 'FLUSH_CONTROL',
               'READ_CONTROL', 'TAG_READ', 'TAG_STATE', 'FILL_STATE', 'CACHE_STATE', 'DIFF']:
    ar, br = records(log, prefix), records(base_log, prefix)
    changes[prefix] = {'records': len(ar), 'baseline_records': len(br), 'same_record_sequence': ar == br,
                       'first_changed_record': next(({'baseline': b, 'ablation': a} for a, b in zip(ar, br) if a != b), None)}
result = {'bindings': protocol['bindings'], 'evidence_sha256': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in [p / 'control.log', p / 'stages.json', base / 'control.log']},
          'stages': stages, 'fixed_dynamic_inputs_equal': True, 'input_cycles': 512,
          'requests': requests, 'responses': responses, 'outstanding': outstanding,
          'baseline_mismatches': int(bdone[0]), 'ablation_mismatches': int(done[0]), 'captured_record_changes': changes,
          'functional_admission': False,
          'scope': 'Fixed captured input trace, two source conditional replacements. Printed DIFF records are limited; unchanged total does not prove identical all-output mismatch locations or universal equivalence.'}
(p / 'fixed_counter_ablation_audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['fixed_dynamic_inputs_equal', 'requests', 'responses', 'baseline_mismatches', 'ablation_mismatches', 'captured_record_changes']}, indent=2))
