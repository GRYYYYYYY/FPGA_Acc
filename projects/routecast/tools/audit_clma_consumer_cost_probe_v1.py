"""Independently bind the completed cost probe; never rerun native routing."""
import hashlib
import json
import re
from pathlib import Path

R = Path(__file__).resolve().parents[1]
D = R / 'experiments/clma_consumer_cost_probe_v1_2026-10-21'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

protocol = json.loads((D / 'protocol.json').read_text())
for path, expected in protocol['bindings'].items():
    assert sha(path) == expected, path
command = json.loads((D / 'command.json').read_text())
for flag, value in {'--route_chan_width':'200', '--num_workers':'1', '--seed':'1',
                    '--max_router_iterations':'100', '--check_route':'full'}.items():
    assert command[command.index(flag) + 1] == value, flag
assert '--route' in command
for name in ['clma.net', 'clma.place', 'clma.blif']:
    original = [p for p in protocol['bindings'] if Path(p).name == name]
    assert len(original) == 1
    assert sha(D / 'native' / name) == protocol['bindings'][original[0]]
log = (D / 'native/native.log').read_text()
assert ' '.join(command) in log
assert 'RouterOpts.check_route: FULL' in log
assert 'Completed routing consistency check successfully.' in log
assert 'Circuit successfully routed with a channel width factor of 200.' in log
assert (D / 'native/output.route').stat().st_size > 0
route_seconds = float(re.search(r'# Routing took ([0-9.]+) seconds', log)[1])
stats = re.search(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)', log)
assert stats
result = json.loads((D / 'result.json').read_text())
assert result['exit_code'] == 0 and result['VPR_success'] and result['full_native_self_check']
assert 0 < route_seconds <= result['native_process_seconds'] <= result['copy_and_native_seconds']
receipt = {
    'input_and_copy_hashes_verified': True, 'native_flags_and_selfcheck_verified': True,
    'routing_log_seconds_rounded': route_seconds,
    'native_work': dict(zip(['NET_operations','connection_operations','heap_pushes','heap_pops'], map(int, stats.groups()))),
    'native_process_seconds': result['native_process_seconds'],
    'bindings': {str(p): sha(p) for p in [Path(__file__), D/'protocol.json', D/'command.json', D/'result.json', D/'native/native.log', D/'native/output.route']},
    'limits': 'Receipt audit only. No rerun, independent physical/canonical/endpoint gate, paired candidate comparison, source capture timing or strict unseen evidence.'
}
(D / 'independent_cost_audit_v1.json').write_text(json.dumps(receipt, indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k != 'bindings'}, indent=2))
