"""Authenticate timed rerun parity and disjoint stage/nested query accounting."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_owned_reverse_run_2026-10-06'
base=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert len(p['cases'])==len(r['rows'])==1
assert (p['cases'][0]['width'],p['cases'][0]['index'])==(32,2)
assert r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(f)==h for f,h in p['sources'].items())
file=out/'w32_m2/result.json';old=base/'w32_m2/result.json'
assert file.read_bytes()==old.read_bytes() and r['rows'][0]['result_sha256']==sha(file)
d=json.loads(file.read_text());timing=out/'w32_m2/phase_times.json';phases=json.loads(timing.read_text())['phases']
for name,t in phases.items():
 assert t['calls']==len(t['per_call_seconds']) and all(v>=0 for v in t['per_call_seconds'])
 assert t['seconds']==sum(t['per_call_seconds'])
assert phases['allocate']['calls']==len(d['allocations'])
assert phases['attempt']['calls']==len(d['attempts'])
assert phases['observe']['calls']==sum('observation' in row for row in d['result']['trace'])
assert phases['native_query']['seconds']<=phases['attempt']['seconds']
assert sum(phases[k]['seconds'] for k in ('allocate','attempt','observe'))<=r['rows'][0]['loop_seconds']
library=ROOT/'experiments/mux_owned_reverse_graph_2026-10-06/search.so'
assert p['binary_sha256']==sha(library)
fixture=library.parent/'fixture_verification.json';contract=library.parent/'contract_verification.json'
assert json.loads(fixture.read_text())['new_binary_sha256']==sha(library)
assert json.loads(contract.read_text())['binary_sha256']==sha(library)
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),fixture_verification_sha256=sha(fixture),contract_verification_sha256=sha(contract),receipt_sha256=sha(out/'receipt.json'),phase_times_sha256=sha(timing),result_sha256=sha(file),baseline_audit_sha256=sha(base/'audit_summary.json'),phase_totals={k:dict(seconds=t['seconds'],calls=t['calls']) for k,t in phases.items()},scope='Byte-identical prospective candidate/allocations/observations/queues/history to independently audited baseline. Disjoint stage totals and nested query subset checked. Single timing run with overhead/concurrent load; no speedup or wholecohort extrapolation.'),indent=2)+'\n');print({k:t['seconds'] for k,t in phases.items()})
