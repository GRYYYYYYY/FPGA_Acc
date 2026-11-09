"""Freeze and audit observed original-reference bus inputs, not predictions."""
import hashlib
import json
import re
from pathlib import Path

p = Path('experiments/full_source_export_original_bus_capture_v18_2026-10-09')
parent = Path('experiments/full_source_export_data_flush_counter_trace_v16_2026-10-09')
protocol = json.loads((p / 'protocol.json').read_text())
for filename, expected in protocol['bindings'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
for name in ['reference.v', 'design.v', 'primitives.v', 'control.py', 'run.py']:
    assert (p / name).read_bytes() == (parent / name).read_bytes()
stages = json.loads((p / 'stages.json').read_text())
assert len(stages) == 3 and all(s['exit_code'] == 0 for s in stages)
log = (p / 'control.log').read_text()
assert 'Fatal' not in log
rx = (r'BUS_INPUT cycle=\s*(\d+) reset=([01]) debugReset=([01]) ready=([01]) '
      r'rsp_valid=([01]) rsp_data=([0-9a-fA-F]+) rsp_error=([01]) accepted=([01]) '
      r'cmd_valid=([01xz]) cmd_address=([0-9a-fA-FxXzZ]+) cmd_size=([01xz]{3})')
keys = ['cycle', 'reset', 'debugReset', 'ready', 'rsp_valid', 'rsp_data', 'rsp_error', 'accepted', 'cmd_valid', 'cmd_address', 'cmd_size']
rows = [dict(zip(keys, match)) for match in re.findall(rx, log)]
assert [int(r['cycle']) for r in rows] == list(range(512))
beats = 0
requests = 0
responses = 0
transactions = []
for row in rows:
    cycle = int(row['cycle'])
    assert row['reset'] == row['debugReset'] == ('1' if cycle <= 2 else '0')
    assert int(row['ready']) == int(beats == 0)
    assert int(row['rsp_valid']) == int(beats > 0)
    assert int(row['rsp_data'], 16) == 0x13 and row['rsp_error'] == '0'
    accepted = row['cmd_valid'] == '1' and row['ready'] == '1'
    assert int(row['accepted']) == int(accepted)
    if row['rsp_valid'] == '1':
        assert transactions and beats > 0
        transactions[-1]['response_cycles'].append(cycle)
        beats -= 1
        responses += 1
    if accepted:
        assert beats == 0 and row['cmd_size'] == '101'
        address = int(row['cmd_address'], 16)
        assert address % 32 == 0
        transactions.append({'accepted_cycle': cycle, 'address': address, 'response_cycles': []})
        requests += 1
        beats = 8
coverage = re.findall(r'IBUS_COVERAGE requests=\s*(\d+) responses=\s*(\d+) outstanding=\s*(\d+)', log)
assert coverage == [(str(requests), str(responses), str(beats))]
assert requests > 0 and responses >= 8
for transaction in transactions:
    expected = list(range(transaction['accepted_cycle'] + 1, min(transaction['accepted_cycle'] + 9, 512)))
    assert transaction['response_cycles'] == expected
assert responses + beats == 8 * requests
done = re.findall(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)', log)
assert len(done) == 1
trace = {'dynamic_inputs': ['reset', 'debugReset', 'ready', 'rsp_valid', 'rsp_data', 'rsp_error'], 'rows': rows,
         'scope': 'Captured original reference inputs before clock edges; request metadata retained. Other top inputs must retain original TB constant assignments.'}
(p / 'frozen_bus_trace.json').write_text(json.dumps(trace, indent=2) + '\n')
audit = {'bindings': protocol['bindings'], 'evidence_sha256': {name: hashlib.sha256((p / name).read_bytes()).hexdigest() for name in ['control.log', 'stages.json', 'frozen_bus_trace.json']},
         'stages': stages, 'cycles': 512, 'requests': requests, 'responses': responses, 'outstanding': beats,
         'transactions': transactions, 'mismatches': int(done[0]), 'functional_admission': False,
         'scope': 'Original-reference instruction transaction input capture. Does not prove export request legality, retirement or universal equivalence.'}
(p / 'bus_capture_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({k: audit[k] for k in ['cycles', 'requests', 'responses', 'outstanding', 'mismatches']}, indent=2))
