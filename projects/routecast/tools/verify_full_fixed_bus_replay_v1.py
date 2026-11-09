"""Audit original-source replay against actual captured baseline records."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_fixed_bus_replay_v19_2026-10-09')
parent = Path('experiments/full_source_export_original_bus_capture_v18_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
assert hashlib.sha256((parent / 'bus_capture_audit.json').read_bytes()).hexdigest() == protocol['parent_capture_audit_sha256']
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py', 'frozen_bus_trace.json']:
    assert (p / name).read_bytes() == (parent / name).read_bytes()
trace = json.loads((p / 'frozen_bus_trace.json').read_text())
case = ' case(i)\n'
for row in trace['rows']:
    case += f" {row['cycle']}: begin iBus_cmd_ready=1'b{row['ready']};iBus_rsp_valid=1'b{row['rsp_valid']};iBus_rsp_payload_data=32'h{row['rsp_data']};iBus_rsp_payload_error=1'b{row['rsp_error']};if(reset!==1'b{row['reset']} || debugReset!==1'b{row['debugReset']}) $fatal(1,\"frozen reset trace mismatch\");end\n"
case += ' default: $fatal(1,"replay index outside frozen trace");\n endcase'
old = " iBus_cmd_ready=(beats==0);iBus_rsp_valid=(beats>0);iBus_rsp_payload_data=32'h00000013;iBus_rsp_payload_error=0;"
original_tb = (parent / 'tb.v').read_text()
assert original_tb.count(old) == 1
assert original_tb.replace(old, case) == (p / 'tb.v').read_text()
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
parent_log = (parent / 'control.log').read_text()
assert 'Fatal' not in log
prefixes = ['BUS_INPUT', 'COUNTER_CONTROL', 'PIPE_BOUNDARY', 'DATA_FLUSH', 'PIPE_NODE',
            'FLUSH_CONTROL', 'READ_CONTROL', 'TAG_READ', 'TAG_STATE', 'FILL_STATE',
            'CACHE_STATE', 'DIFF', 'IBUS_COVERAGE', 'ROUTECAST_FULL_COMPARE_DONE']
counts = {}
for prefix in prefixes:
    rx = r'@"(' + prefix + r'[^\n]*?)\\n"'
    actual = re.findall(rx, log)
    expected = re.findall(rx, parent_log)
    assert actual == expected, prefix
    counts[prefix] = len(actual)
assert counts['BUS_INPUT'] == 512 and counts['ROUTECAST_FULL_COMPARE_DONE'] == 1
result = {'bindings': protocol['bindings'], 'evidence_sha256': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in [p / 'control.log', p / 'stages.json', parent / 'control.log']},
          'stages': stages, 'matched_record_counts': counts, 'replay_fidelity_on_captured_records': True,
          'functional_admission': False,
          'scope': 'Exact fixed input generator substitution and captured diagnostic records match original failing baseline. Does not prove unobserved state equivalence or repair original functional failure.'}
(p / 'fixed_replay_audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(counts, indent=2))
