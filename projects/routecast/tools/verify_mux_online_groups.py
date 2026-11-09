"""Reconstruct online undirected conflict components from direct observations."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_allfanin_group32_v2_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12;rows=[]
for row in r['rows']:
 if row['status']=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];f=out/f'w{w}_m{i}/prediction.json';assert sha(f)==row['prediction_sha256'];p=json.loads(f.read_text());edges={};checks=0
 for j,e in enumerate(p['events']):
  if e['type']!='CONFLICT_GROUP':continue
  a=e['failed_query']['net_id']
  for b in e['direct_blocker_NETs']:edges.setdefault(a,set()).add(b);edges.setdefault(b,set()).add(a)
  group={a};todo=[a]
  while todo:
   for b in edges.get(todo.pop(),()):
    if b not in group:group.add(b);todo.append(b)
  assert sorted(group)==e['group_NETs'] and len(group)<=e['limit']==16
  release=p['events'][j+1];assert release['type']=='RELEASE' and release['blocker_NETs']==sorted(group)
  assert {k for owners in release['owners'].values() for k in owners}==set(e['direct_blocker_NETs'])
  assert set(map(int,release['released_unions']))==group
  checks+=1
 assert checks==p['repairs']<=32
 rows.append(dict(width=w,index=i,groups_checked=checks,status=p['status']))
(out/'online_group_verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent online connected-component reconstruction from direct owner observations, group release sets and bounds. Does not prove complete native routing.'),indent=2)+'\n');print(rows)
