"""Available prospective cache-cohort result parity and owned-cache accounting."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_owned_bound_cache_cohort_2026-10-06';old=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');assert p['cases']==read(old/'protocol.json')['cases'] and len(p['cases'])==12
assert all(sha(f)==h for f,h in p['sources'].items())
assert p['binary_sha256']==sha(ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so')
rows=[]
for c in p['cases']:
 w,i=c['width'],c['index'];work=out/f'w{w}_m{i}';file=work/'result.json'
 seed=read(ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json')
 if seed['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':rows.append(dict(width=w,index=i,status='FROZEN_INITIAL_SKIP'));continue
 if not file.exists() or not (work/'cache_stats.json').exists():rows.append(dict(width=w,index=i,status='PENDING'));continue
 original=old/f'w{w}_m{i}/result.json';assert original.read_bytes()==file.read_bytes()
 d=read(file);cache=read(work/'cache_stats.json');timing=read(work/'phase_times.json')['phases'];count=0
 for attempt in d['attempts']:
  u=attempt['update'];count+=len(u['incremental']['events'])
  if u['repair']:
   count+=sum(e['type'] in ('QUERY','BUDGET_WITNESS') for e in u['repair']['events'])
   count+=int((u['repair'].get('failure') or {}).get('status') in ('NO_BOUNDED_RELAXED_WITNESS','NO_CAPACITY_BLOCKER_ON_WITNESS'))
 assert cache['hits']+cache['misses']==timing['native_query']['calls']==count
 assert cache['payload_bytes']<=cache['payload_limit_bytes']==p['cache_payload_limit_bytes']
 for phase in timing.values():assert phase['calls']==len(phase['per_call_seconds']) and phase['seconds']==sum(phase['per_call_seconds'])
 assert timing['allocate']['calls']==len(d['allocations']) and timing['attempt']['calls']==len(d['attempts'])
 assert all(sha(f)==h for f,h in c['inputs'].items())
 rows.append(dict(width=w,index=i,status=d['result']['status'],result_sha256=sha(file),cache_sha256=sha(work/'cache_stats.json'),phase_times_sha256=sha(work/'phase_times.json'),cache=cache))
(out/'cache_parity_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),protocol_sha256=sha(out/'protocol.json'),baseline_audit_sha256=sha(old/'audit_summary.json'),rows=rows,pending=sum(r['status']=='PENDING' for r in rows),scope='Available real outputs byte-identical to six-audited baseline, full12 frozen cases retained with pending/skips explicit. Cache query counts independently derived from actual stage/repair events, payload bounded. Complete sketch still requires native content qualification; no matched lifecycle gain/generalization.'),indent=2)+'\n');print([(r['width'],r['index'],r['status']) for r in rows])
