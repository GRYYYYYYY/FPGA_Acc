"""Terminal cache/source/count accounting; heuristic routing may differ baseline."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_heuristic_single_scan_cohort_2026-10-07'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');r=read(out/'receipt.json');assert len(r['rows'])==len(p['cases'])==12 and r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(f)==h for f,h in p['sources'].items())
rows=[];uncertified=0
for case,row in zip(p['cases'],r['rows']):
 w,i=case['width'],case['index'];assert (w,i)==(row['width'],row['index'])
 if row['status']=='PRIOR_ALLOCATION_SKIP':rows.append(row);continue
 work=out/f'w{w}_m{i}';file=work/'result.json';assert sha(file)==row['result_sha256'];d=read(file);stats=read(work/'cache_stats.json');phases=read(work/'phase_times.json')['phases'];queries=0
 for attempt in d['attempts']:
  u=attempt['update'];queries+=len(u['incremental']['events'])
  if u['repair']:
   queries+=sum(e['type'] in ('QUERY','BUDGET_WITNESS') for e in u['repair']['events'])
   queries+=int((u['repair'].get('failure') or {}).get('status') in ('NO_BOUNDED_RELAXED_WITNESS','NO_CAPACITY_BLOCKER_ON_WITNESS'))
 assert queries==stats['hits']+stats['misses']==phases['native_query']['calls']
 assert stats['payload_bytes']<=stats['payload_limit_bytes']==p['cache_payload_limit_bytes']
 assert row['routing_status']==d['result']['status']
 assert row['status']==(d['candidate_model_gate']['status'] if row['routing_status']=='COMPLETE_CANDIDATE' else row['routing_status'])
 for spec in d['allocations']:
  if spec['valid'] and spec['budget_policy']=='HEURISTIC_PRESERVE_WITH_CONDITIONAL_FLOORS':
   from fractions import Fraction as F
   uncertified+=int(F(spec['budget_cpd_ns'])>F(d.get('candidate_model_gate',{}).get('target_cpd_ns',read(ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json')['target_cpd_ns'])))
 assert all(sha(f)==h for f,h in case['inputs'].items())
 rows.append(dict(width=w,index=i,status=row['status'],queries=queries,cache=stats,result_sha256=sha(file),cache_sha256=sha(work/'cache_stats.json'),phase_sha256=sha(work/'phase_times.json')))
(out/'cache_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(out/'receipt.json'),rows=rows,uncertified_preserved_allocations=uncertified,scope='All12 terminal source/input/case/cache byte limit and event-derived query counts, overall actual-model gate versus raw routing status. Heuristic envelope failures explicit, not required to match certified reroute. Full physical/native quality proofs separate.'),indent=2)+'\n');print('cache verified; heuristic envelope failures',uncertified)
