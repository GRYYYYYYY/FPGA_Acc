"""Focused retrospective avoid-frontier lower bounds; no online oracle input."""
import json
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06';out=ROOT/'experiments/mux_quadratic_repair_detours_2026-10-06';out.mkdir(exist_ok=True);file=base/'w8_m1/result.json';data=json.loads(file.read_text());p=json.loads((base/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(8,1));ctx=PersistentRCContext(case['old']);ctx.bind_endpoints(case['target']);attempt=data['attempts'][0];spec=data['allocations'][attempt['allocation_index']];events=[e for e in attempt['update']['repair']['events'] if e['type']=='RELEASE'];frequency=Counter((e['failed_query']['connection_id'],tuple(e['blocker_NETs'])) for e in events);rows=[]
for key,count in frequency.most_common(2):
 event=next(e for e in events if (e['failed_query']['connection_id'],tuple(e['blocker_NETs']))==key);q=event['failed_query'];ban=set(event['frontier'])
 for peer in ctx.context[5]:
  if (peer['source'],peer['sink'])==(q['source'],q['sink']):ban.update(spec['restrictions'].get(str(peer['net_id']),[]))
 witness=shortest_delay(ctx,q['source'],q['sink'],ban);dist=witness['distances'];pred=witness['predecessor_slots'];f=ctx.rc.fields
 if q['source'] not in ban and f['capacities'][q['source']]>0:assert dist[q['source']]==0
 for u,du in dist.items():
  assert u not in ban
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if v not in ban and f['capacities'][v]>0:assert v in dist and dist[v]<=du+ctx.rc.increments[slot]
 slot_sources={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 for v in dist:
  node=v;seen=set()
  while node!=q['source']:
   assert node not in seen;seen.add(node);slot=pred[node];u=slot_sources[slot];assert f['dest_ranks'][slot]==node and dist[node]==dist[u]+ctx.rc.increments[slot];node=u
 budget=min(int(F(spec['budgets_ns'][str(q['connection_id'])])*ctx.rc.scale/10**9),ctx.rc.scale//10**9);minimum=witness['minimum'];rows.append(dict(query=q,repetitions=count,owners=list(key[1]),forbidden=sorted(ban),budget=budget,minimum=minimum,within_budget=minimum is not None and minimum<=budget,certificate=witness))
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),result_sha256=sha(file),rows=rows,scale=ctx.rc.scale,scope='Retrospective first-attempt w8m1 two most frequent repair pairs. Zero occupancy relaxed shortest delay avoiding entire observed frontier; closed reachability/all-edge inequalities/rooted predecessor witnesses checked. Shared authenticated integer RC; no global capacity/complete route or native STA proof; no input to running experiment.'),indent=2)+'\n');print([(r['query']['connection_id'],r['repetitions'],r['within_budget']) for r in rows])
