"""Authenticate timed rerun parity and disjoint stage/nested query accounting."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_native_internal_profile_run_2026-10-06'
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
detail_file=out/'w32_m2/query_times.json';detail=json.loads(detail_file.read_text())['phases']
for name,t in detail.items():
 assert t['calls']==len(t['per_call_seconds']) and all(v>=0 for v in t['per_call_seconds'])
 assert t['seconds']==sum(t['per_call_seconds'])
expected_queries=0;expected_found=0
for attempt in d['attempts']:
 update=attempt['update'];events=list(update['incremental']['events'])
 if update['repair']:
  events += [event for event in update['repair']['events'] if event['type'] in ('QUERY','BUDGET_WITNESS')]
  expected_queries += int((update['repair'].get('failure') or {}).get('status')=='NO_BOUNDED_RELAXED_WITNESS')
 expected_queries += len(events)
 expected_found += sum(event['answer']['status']=='FOUND' for event in events)
assert detail['rc_query']['calls']==phases['native_query']['calls']==expected_queries
assert detail['path_validation']['calls']==expected_found
assert all(sha(f)==h for f,h in p['cases'][0]['inputs'].items())
assert detail['rc_query']['seconds']<=phases['native_query']['seconds']
assert detail['path_validation']['calls']<=detail['rc_query']['calls']
assert detail['set_other']['calls']>=detail['rc_query']['calls']
native_file=out/'w32_m2/native_phase_times.json';native=json.loads(native_file.read_text())
assert len(native['per_query_ns'])==expected_queries
assert all(len(row)==4 and all(type(v) is int and v>=0 for v in row) and row[3]==0 for row in native['per_query_ns'])
assert native['totals_ns']==[sum(row[k] for row in native['per_query_ns']) for k in range(4)]
assert all(sum(row)/10**9<=seconds for row,seconds in zip(native['per_query_ns'],detail['rc_query']['per_call_seconds']))
assert p['binary_sha256']==sha(ROOT/'experiments/mux_native_phase_profile_2026-10-06/search.so')
fixture_file=ROOT/'experiments/mux_native_phase_profile_2026-10-06/fixture_verification.json';fixture=json.loads(fixture_file.read_text())
assert fixture['new_binary_sha256']==p['binary_sha256'] and fixture['queries']==1000
error_file=ROOT/'experiments/mux_native_phase_profile_2026-10-06/error_verification.json';errors=json.loads(error_file.read_text())
assert errors['new_binary_sha256']==p['binary_sha256'] and len(errors['rows'])==5
assert errors['old_binary_sha256']==fixture['old_binary_sha256']
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(out/'receipt.json'),native_phase_times_sha256=sha(native_file),fixture_verification_sha256=sha(fixture_file),error_verification_sha256=sha(error_file),native_phase_seconds=dict(zip(native['phase_names'],[v/10**9 for v in native['totals_ns']])),phase_times_sha256=sha(timing),query_times_sha256=sha(detail_file),query_component_totals={k:dict(seconds=t['seconds'],calls=t['calls']) for k,t in detail.items()},result_sha256=sha(file),baseline_audit_sha256=sha(base/'audit_summary.json'),phase_totals={k:dict(seconds=t['seconds'],calls=t['calls']) for k,t in phases.items()},scope='Byte-identical prospective candidate/allocations/observations/queues/history to independently audited baseline. Disjoint stage totals and nested query subset checked. Single timing run with overhead/concurrent load; no speedup or wholecohort extrapolation.'),indent=2)+'\n');print({'native_phase_seconds':dict(zip(native['phase_names'],[v/10**9 for v in native['totals_ns']])),'stage_seconds':{k:t['seconds'] for k,t in phases.items()},'query_components':{k:dict(seconds=t['seconds'],calls=t['calls']) for k,t in detail.items()}})
