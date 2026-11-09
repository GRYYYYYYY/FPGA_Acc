"""Independent Tarjan SCC and raw release-event provenance check."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_conflict_groups_2026-10-06';parent=ROOT/'experiments/mux_allfanin_priority32_2026-10-06'
r=json.loads((out/'receipt.json').read_text());assert r['parent_receipt_sha256']==sha(parent/'receipt.json');checked=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];f=out/f'w{w}_m{i}.json';assert sha(f)==row['sha256'];d=json.loads(f.read_text());pf=parent/f'w{w}_m{i}/prediction.json';assert sha(pf)==d['prediction_sha256'];p=json.loads(pf.read_text());adj={};counts=Counter();resources=Counter()
 releases=[(j,e) for j,e in enumerate(p['events']) if e['type']=='RELEASE'];assert len(releases)==len(d['release_evidence'])
 for (j,e),ev in zip(releases,d['release_evidence']):
  a=e['failed_query']['net_id'];assert ev==dict(event_index=j,source_net=a,blocker_nets=e['blocker_NETs'],frontier=e['frontier'])
  for b in e['blocker_NETs']:
   adj.setdefault(a,set()).add(b);adj.setdefault(b,set());counts[a,b]+=1
   for n,owners in e['owners'].items():
    if b in owners:assert int(n) in e['released_unions'][str(b)];resources[a,b,int(n)]+=1
 index={};low={};stack=[];active=set();parts=[]
 def visit(v):
  index[v]=low[v]=len(index);stack.append(v);active.add(v)
  for z in adj[v]:
   if z not in index:visit(z);low[v]=min(low[v],low[z])
   elif z in active:low[v]=min(low[v],index[z])
  if low[v]==index[v]:
   part=[]
   while True:
    z=stack.pop();active.remove(z);part.append(z)
    if z==v:break
   if len(part)>1:parts.append(sorted(part))
 for v in adj:
  if v not in index:visit(v)
 assert sorted(parts)==sorted(g['nets'] for g in d['groups'])
 for g in d['groups']:
  expected={(a,b):c for (a,b),c in counts.items() if a in g['nets'] and b in g['nets']}
  assert expected=={(e['source_net'],e['owner_net']):e['releases'] for e in g['internal_edges']}
  for e in g['internal_edges']:
   a,b=e['source_net'],e['owner_net'];assert {str(n):c for (x,y,n),c in resources.items() if (x,y)==(a,b)}==e['blocked_node_counts']
 checked.append(dict(width=w,index=i,groups=len(parts),releases=len(releases)))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=checked,scope='Independent Tarjan membership and exact archived event/resource frequency checks; not a physical cut or infeasibility proof.'),indent=2)+'\n');print(checked)
