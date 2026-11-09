"""Check archived in-run shortest witnesses by certificate algebra."""
import json,sys
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w,i=map(int,sys.argv[1:]);out=ROOT/'experiments/mux_owned_bound_cache_cohort_2026-10-06';file=out/f'w{w}_m{i}/result.json';d=json.loads(file.read_text());p=json.loads((out/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(w,i));ctx=PersistentRCContext(case['target']);f=ctx.rc.fields;inc=ctx.rc.increments;slot_source={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};checked=labels=0
for entry in d['result']['trace']:
 obs=entry.get('observation')
 if not obs or 'witness' not in obs:continue
 q=obs['query'];assert q in ctx.context[5];source,sink=q['source'],q['sink'];bans=set()
 for query in ctx.context[5]:
  if (query['source'],query['sink'])==(source,sink):bans.update(entry['restrictions'].get(str(query['net_id']),[]))
 cert=obs['witness'];dist={int(n):v for n,v in cert['distances'].items()};pred={int(n):s for n,s in cert['predecessor_slots'].items()};assert not bans&set(dist)
 if source in bans or f['capacities'][source]<=0:assert not dist
 else:assert dist[source]==0 and set(pred)==set(dist)-{source}
 for u,value in dist.items():
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if v in bans or f['capacities'][v]<=0:continue
   assert v in dist and dist[v]<=value+inc[slot]
 rooted={source} if source in dist else set()
 for n in pred:
  trail=[];seen=set()
  while n not in rooted:
   assert n not in seen;seen.add(n);trail.append(n);slot=pred[n];u=slot_source[slot];assert f['dest_ranks'][slot]==n and dist[n]==dist[u]+inc[slot];n=u
  rooted.update(trail)
 assert cert['minimum']==dist.get(sink);path=[];node=sink
 if sink in dist:
  while node!=source:path.append(node);node=slot_source[pred[node]]
  path.append(source);path.reverse()
 assert cert['path_nodes']==path;checked+=1;labels+=len(dist)
(file.parent/'observation_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),witnesses=checked,finite_labels=labels,scope='Archived observation exact integer shortest-delay certificate via complete edge/reachable closure and predecessor-root equality; endpoint-pair bans and physical-rank witness nodes. Ownership checked separately against original XML. Shared RC loader, no nativeSTA.'),indent=2)+'\n');print(w,i,'verified',checked,'in-run shortest witnesses',flush=True)
