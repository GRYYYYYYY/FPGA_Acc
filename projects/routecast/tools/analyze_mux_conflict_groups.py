"""Observed release dependency SCCs; no inference of global unrouteability."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/mux_allfanin_priority32_2026-10-06'
out=ROOT/'experiments/mux_conflict_groups_2026-10-06';out.mkdir()
r=json.loads((parent/'receipt.json').read_text());rows=[]
for row in r['rows']:
 w,i=row['width'],row['index']
 if row['status']=='ALLOCATION_NOT_SUBMITTED':rows.append(dict(width=w,index=i,status=row['status']));continue
 file=parent/f'w{w}_m{i}/prediction.json';assert sha(file)==row['prediction_sha256'];p=json.loads(file.read_text())
 deps=defaultdict(set);pairs=Counter();nodes=defaultdict(Counter);evidence=[]
 for event_index,e in enumerate(p['events']):
  if e['type']!='RELEASE':continue
  src=e['failed_query']['net_id'];owners={int(n):ks for n,ks in e['owners'].items()}
  assert set(owners)==set(e['frontier'])
  assert set(e['blocker_NETs'])=={k for ks in owners.values() for k in ks}
  for n,ks in owners.items():
   for k in ks:assert k!=src and n in e['released_unions'][str(k)]
  for dst in e['blocker_NETs']:
   deps[src].add(dst);pairs[src,dst]+=1
   for n,ks in owners.items():
    if dst in ks:nodes[src,dst][n]+=1
  evidence.append(dict(event_index=event_index,source_net=src,blocker_nets=e['blocker_NETs'],frontier=e['frontier']))
 vertices=set(deps)|{v for vs in deps.values() for v in vs}
 def reach(src):
  seen={src};todo=[src]
  while todo:
   for v in deps.get(todo.pop(),()):
    if v not in seen:seen.add(v);todo.append(v)
  return seen
 closure={v:reach(v) for v in vertices};remaining=set(vertices);groups=[]
 while remaining:
  v=min(remaining);group=sorted(n for n in remaining if n in closure[v] and v in closure[n]);remaining-=set(group)
  if len(group)>1:
   internal=[dict(source_net=a,owner_net=b,releases=c,blocked_node_counts={str(n):x for n,x in nodes[a,b].items()}) for (a,b),c in sorted(pairs.items()) if a in group and b in group]
   groups.append(dict(nets=group,internal_edges=internal))
 result=dict(width=w,index=i,prediction_sha256=sha(file),groups=groups,release_evidence=evidence)
 f=out/f'w{w}_m{i}.json';f.write_text(json.dumps(result,indent=2)+'\n');rows.append(dict(width=w,index=i,groups=[g['nets'] for g in groups],sha256=sha(f)))
 print(w,i,[(g['nets'],sum(x['releases'] for x in g['internal_edges'])) for g in groups],flush=True)
(out/'receipt.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),source_sha256=sha(Path(__file__)),rows=rows,scope='SCCs of observed failed-NET to released-owner dependencies. Ownership associations checked against archived released unions; RR ranks, not physical node IDs. Sequential observations do not prove simultaneous capacity cuts, infeasibility, or identical state cycles.'),indent=2)+'\n')
