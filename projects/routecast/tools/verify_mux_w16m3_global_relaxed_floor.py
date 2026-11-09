"""Certify shortest bounds by inequalities and rooted predecessor witnesses."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,deque
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_w16m3_global_relaxed_floor_2026-10-07';r=json.loads((out/'receipt.json').read_text());assert all(sha(f)==h for f,h in r['bindings'].items());p=json.loads((ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07/protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(16,3));ctx=PersistentRCContext(case['target']);assert ctx.rc.scale==r['scale'];fields=ctx.rc.fields;slot_source={s:u for u in range(len(ctx.context[2])) for s in range(fields['row_offsets'][u],fields['row_offsets'][u+1])};certs=json.loads((out/'certificates.json').read_text())
for cert in certs:
 dist={int(k):v for k,v in cert['distances'].items()};pred={int(k):v for k,v in cert['predecessor_slots'].items()};source=cert['source'];bans=set(cert['bans']);assert source not in bans and dist[source]==0 and set(pred)==set(dist)-{source};assert not bans&set(dist)
 for u,value in dist.items():
  assert fields['capacities'][u]>0
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   v=fields['dest_ranks'][slot]
   if v in bans or fields['capacities'][v]<=0:continue
   assert v in dist and dist[v]<=value+ctx.rc.increments[slot]
 rooted={source}
 for n in pred:
  trail=[];seen=set()
  while n not in rooted:
   assert n not in seen;seen.add(n);trail.append(n);slot=pred[n];u=slot_source[slot];assert fields['dest_ranks'][slot]==n and dist[n]==dist[u]+ctx.rc.increments[slot];n=u
  rooted.update(trail)
g=json.loads((ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w16_timing_graph.json').read_text());m=json.loads((ROOT/'experiments/mux_full_timing_rr_2026-10-06/w16.json').read_text());a=json.loads((ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w16_m3.json').read_text());d=json.loads((ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07/w16_m3/result.json').read_text());adj=defaultdict(list);ind={int(n):0 for n in g['nodes']}
for eid,e in g['edges'].items():
 if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
queue=deque(n for n in ind if not ind[n]);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  ind[v]-=1
  if not ind[v]:queue.append(v)
assert len(order)==len(ind)
for row in r['rows']:
 s=d['allocations'][row['allocation']];pair_bans={}
 for q in ctx.context[5]:pair_bans.setdefault((q['source'],q['sink']),set()).update(s['restrictions'].get(str(q['net_id']),[]))
 for q in ctx.context[5]:
  cid=str(q['connection_id']);cert=certs[row['certificate_indices'][cid]];assert cert['source']==q['source'] and set(cert['bans'])==pair_bans[(q['source'],q['sink'])];assert F(row['minimum_ns'][cid])==F(cert['distances'][str(q['sink'])]*10**9,r['scale'])
 tail={n:F(0) for n in order}
 for u in reversed(order):
  for v,eid in adj[u]:
   cid=a['edge_connection_ids'].get(eid);delay=F(row['minimum_ns'][str(cid)])+F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9 if cid is not None else F(g['edges'][eid]['max_delay_seconds'])*10**9;tail[u]=max(tail[u],delay+tail[v])
 assert max(tail.values())==F(row['relaxed_cpd_ns']);assert row['relaxed_target_pass']==(max(tail.values())<=F(row['target_ns']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),certificates=len(certs),allocations=2,scope='Independent edge inequalities/reachable closure/acyclic rooted witnesses certify integer shortest bounds; backward whole-DAG timing versus forward producer. Shared graph loader; not independent XML RC nor native STA/simultaneous capacity proof.'),indent=2)+'\n');print('Verified',len(certs),'shortest certificates and two backward-DAG values',flush=True)
