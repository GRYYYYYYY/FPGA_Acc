"""Prospective exact parity except documented unused-alpha diagnostic removal."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_lazy_budget_cache_cohort_2026-10-06';base=ROOT/'experiments/mux_owned_bound_cache_cohort_2026-10-06'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');assert p['cases']==read(base/'protocol.json')['cases'] and len(p['cases'])==12
assert all(sha(f)==h for f,h in p['sources'].items())
policies={'INITIAL_NET_SLACK_VECTOR','PRESERVE_INITIAL_WITH_CONDITIONAL_FLOORS'}
def normalize(value,new):
 if isinstance(value,list):return [normalize(v,new) for v in value]
 if isinstance(value,dict):
  value=dict(value)
  if value.get('budget_policy') in policies:
   assert 'interpolation' in value
   if new:assert value['interpolation'] is None
   else:assert value['interpolation'] is not None
   del value['interpolation']
  return {k:normalize(v,new) for k,v in value.items()}
 return value
rows=[]
for c in p['cases']:
 w,i=c['width'],c['index'];file=out/f'w{w}_m{i}/result.json'
 seed=read(ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json')
 if seed['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':rows.append(dict(width=w,index=i,status='FROZEN_INITIAL_SKIP'));continue
 if not file.exists() or not (file.parent/'cache_stats.json').exists():rows.append(dict(width=w,index=i,status='PENDING'));continue
 old=base/f'w{w}_m{i}/result.json';d=read(file);b=read(old)
 assert normalize(d,True)==normalize(b,False)
 # Actual staged native answers/history/ledger must match without normalization.
 assert d['attempts']==b['attempts']
 assert all(sha(f)==h for f,h in c['inputs'].items())
 rows.append(dict(width=w,index=i,status=d['result']['status'],result_sha256=sha(file),baseline_result_sha256=sha(old),skipped_interpolations=sum(a['budget_policy'] in policies for a in d['allocations'])))
(out/'semantic_parity_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),protocol_sha256=sha(out/'protocol.json'),baseline_audit_sha256=sha(base/'audit_summary.json'),rows=rows,pending=sum(r['status']=='PENDING' for r in rows),scope='Exact whole result structure equality after removing ONLY unused interpolation fields for initial/preserved policies; new fields explicitly null, old computed diagnostics. Actual staged native answers/records/repair histories equal without normalization. Full12 cases, skips/pending explicit. Not byte-identical result file or fresh native acceptance claim.'),indent=2)+'\n');print([(r['width'],r['index'],r['status']) for r in rows])
