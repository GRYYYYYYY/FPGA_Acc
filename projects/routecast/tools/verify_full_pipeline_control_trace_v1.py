"""Authenticate frozen pipeline telemetry, without functional admission."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_pipeline_control_trace_v14_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
assert 'Fatal' not in log
manifest = json.loads((p / 'observed_nodes.json').read_text())
names = [n for n, _ in manifest['observed']]
assert len(names) == len(set(names)) == 14
records = re.findall(r'PIPE_NODE cycle=\s*(\d+) net=(\S+) value=([01xz])', log)
assert len(records) == 141 * 14
values = {}
for cycle, net, value in records:
    assert net in names
    assert (int(cycle), net) not in values
    values[int(cycle), net] = value
assert set(values) == {(cycle, net) for cycle in range(141) for net in names}
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
parent = Path('experiments/full_source_export_ibus_flush_control_trace_v12_2026-10-09')
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes(), name
first_x = {net: next((cycle for cycle in range(141) if values[cycle, net] in 'xz'), None) for net in names}
audit = {'bindings': protocol['bindings'], 'evidence_sha256': {name: hashlib.sha256((p / name).read_bytes()).hexdigest() for name in ['control.log', 'stages.json', 'observed_nodes.json']},
         'stages': stages, 'observations': [{'cycle': cycle, 'values': {net: values[cycle, net] for net in names}} for cycle in range(141)],
         'first_unknown_by_node': first_x, 'mismatches': int(done[0]),
         'unobserved_aliases': manifest['not_direct_LUT_outputs'], 'functional_admission': False,
         'scope': '14 combinational outputs on original failing trace. No captured boundary-state values, universal sequential equivalence or physical initialization proof.'}
(p / 'pipeline_trace_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({'records': len(records), 'first_unknown_by_node': first_x, 'cycle4': audit['observations'][4], 'mismatches': int(done[0])}, indent=2))
