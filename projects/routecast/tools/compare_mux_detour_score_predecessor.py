"""Bind actual fixed-cohort selection-policy outcomes; partial counts are not QoR."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'experiments/mux_critical_release_online_loop_2026-10-06'
new=ROOT/'experiments/mux_detour_score_online_loop_2026-10-06'
rows=[]
for file in sorted(new.glob('w*_m*/result.json')):
 previous=old/file.relative_to(new)
 a=json.loads(previous.read_text());b=json.loads(file.read_text())
 x=a['allocations'][0];y=b['allocations'][0]
 assert {k:v for k,v in y.items() if k!='total_floor_increase_ns'}==x
 def selected(d):
  return [t['restrictions'] for t in d['result']['trace']]
 rows.append(dict(case=file.parent.name,old_sha256=sha(previous),new_sha256=sha(file),initial_vector_equal=True,selection_changed=selected(a)!=selected(b),old_status=a['result']['status'],new_status=b['result']['status'],old_completed=a['result']['candidate']['completed_connections'],new_completed=b['result']['candidate']['completed_connections']))
(new/'predecessor_comparison.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),rows=rows,scope='Actual completed-file snapshot, exact initial allocation equality excluding added score field. Changed trace restrictions demonstrate real selection differences. Partial coverage is not accepted QoR or lifecycle benefit; missing cases remain pending.'),indent=2)+'\n')
for row in rows:print(row['case'],row['selection_changed'],row['old_completed'],row['new_completed'])
