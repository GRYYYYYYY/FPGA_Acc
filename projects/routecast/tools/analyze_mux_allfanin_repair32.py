"""Frozen max4/max32 cohort comparison and repeated-owner evidence."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_allfanin_reroute_2026-10-06'
out=ROOT/'experiments/mux_allfanin_repair32_2026-10-06'
a=json.loads((base/'receipt.json').read_text());b=json.loads((out/'receipt.json').read_text());assert len(a['rows'])==len(b['rows'])==12
rows=[]
for x,y in zip(a['rows'],b['rows']):
 assert (x['width'],x['index'])==(y['width'],y['index'])
 row=dict(width=y['width'],index=y['index'],max4_status=x['status'],max32_status=y['status'])
 if y['status']!='ALLOCATION_NOT_SUBMITTED':
  f=out/f"w{y['width']}_m{y['index']}/prediction.json";assert sha(f)==y['prediction_sha256'];p=json.loads(f.read_text())
  releases=[e for e in p['events'] if e['type']=='RELEASE'];owners=Counter(n for e in releases for n in e['blocker_NETs'])
  row.update(max4_completed=x['completed'],max32_completed=y['completed'],max4_seconds=x['stage_seconds'],max32_seconds=y['stage_seconds'],repairs=p['repairs'],repeated_owner_counts={str(n):c for n,c in owners.items() if c>1},release_sequence=[dict(failed_connection=e['failed_query']['connection_id'],blocker_NETs=e['blocker_NETs']) for e in releases],failure=y['failure'])
 rows.append(row)
(out/'comparison.json').write_text(json.dumps(dict(max4_receipt_sha256=sha(base/'receipt.json'),max32_receipt_sha256=sha(out/'receipt.json'),analyzer_sha256=sha(Path(__file__)),rows=rows,scope='One frozen run per bound; repeated ownership releases are observed, not a proof of identical full-state cycles. Stage timings exclude preparation and native quality gates.'),indent=2)+'\n')
print([(r['width'],r['index'],r.get('max32_completed')) for r in rows])
