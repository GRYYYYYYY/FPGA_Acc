"""Compare actual physical routing and exclusions, independently of score counters."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];old=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06';new=ROOT/'experiments/mux_preserved_budget_online_loop_2026-10-06';rows=[]
def paths(c):return sorted((r['connection_id'],r['net_id'],r['source'],r['sink'],tuple(r['answer']['physical_edge_ids'])) for r in c['records'])
for file in sorted(new.glob('w*_m*/result.json')):
 prior=old/file.relative_to(new);a=json.loads(prior.read_text());b=json.loads(file.read_text());assert a['allocations'][0]=={k:v for k,v in b['allocations'][0].items() if k!='budget_policy'}
 at=a['result']['trace'];bt=b['result']['trace'];comparisons=[]
 for j,(x,y) in enumerate(zip(at,bt)):
  comparisons.append(dict(attempt=j,restrictions_equal=x['restrictions']==y['restrictions'],paths_equal=paths(x['candidate'])==paths(y['candidate']),old_completed=x['candidate']['completed_connections'],new_completed=y['candidate']['completed_connections']))
 rows.append(dict(case=file.parent.name,old_sha256=sha(prior),new_sha256=sha(file),initial_allocation_equal=True,old_attempts=len(at),new_attempts=len(bt),old_status=a['result']['status'],new_status=b['result']['status'],comparisons=comparisons))
(new/'predecessor_comparison.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),rows=rows,scope='Completed-file snapshot exact initial allocation and perattempt physical path/exclusion comparisons. Final counts do not prove identical routes; missing cases pending. No acceptance or lifecycle benefit inference.'),indent=2)+'\n')
for r in rows:print(r['case'],'path differences',sum(not x['paths_equal'] for x in r['comparisons']),'exclusion differences',sum(not x['restrictions_equal'] for x in r['comparisons']))
