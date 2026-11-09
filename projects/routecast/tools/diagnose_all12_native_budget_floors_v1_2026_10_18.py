"""Exact relaxed floors for every violating connection in all12 historical targets."""
import json,heapq,time,hashlib
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
from class_cached_rc_endpoint_context_v1 import load_endpoints
R=Path(__file__).resolve().parents[1];D=R/'experiments/all12_native_budget_floors_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases'];native=load(R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json');plans=[]
for c in cases:
 meta=load(c['target']);budget=load(c['budget']);v=next(x for x in native['rows'] if (x['width'],x['index'])==(c['width'],c['index']));qs={q['connection_id']:q for q in meta['connections']}
 for cid in v['violation_ids']:plans.append(dict(width=c['width'],index=c['index'],endpoint=c['target'],query=qs[cid],budget_ns=budget['budgets_ns'].get(str(cid),budget['default_budget_ns'])))
bindings[str(Path(__file__))]=sha(__file__)
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,plans=plans,policy='All violating connections from all12 archived development targets; exact positive-capacity relaxed graph floors; ignore owners/shared-parent constraints. No budget change, native output selection or new native runs.'),f,indent=2);f.write('\n')
rows=[];certs=[];start=time.perf_counter()
for width in (8,16,32):
 selected=[p for p in plans if p['width']==width];graph,digest,nodes,fields,rc,queries=load_endpoints(selected[0]['endpoint']);bindings[str(graph)]=digest;assert all(x>=0 for x in rc.increments)
 groups=defaultdict(list)
 for plan in selected:groups[plan['query']['source']].append(plan)
 for source,group in sorted(groups.items()):
  targets={p['query']['sink'] for p in group};remaining=set(targets);dist={source:rc.initial(source)};pred={};queue=[(dist[source],source)];settled=set()
  while queue and remaining:
   value,u=heapq.heappop(queue)
   if u in settled or value!=dist[u]:continue
   settled.add(u);remaining.discard(u)
   for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
    v=fields['dest_ranks'][slot]
    if fields['capacities'][v]<=0:continue
    candidate=value+rc.increments[slot]
    if candidate<dist.get(v,candidate+1):dist[v]=candidate;pred[v]=(u,slot);heapq.heappush(queue,(candidate,v))
  assert not remaining,'Native path exists so relaxed targets must be reachable'
  clip=max(dist[t] for t in targets);potential={u:value for u,value in dist.items() if value<clip}
  # Independent certificate check: all positive-capacity arcs, no search replay.
  assert potential.get(source,clip)<=rc.initial(source)
  checked=0
  for u in range(len(nodes)):
   if fields['capacities'][u]<=0:continue
   for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
    v=fields['dest_ranks'][slot]
    if fields['capacities'][v]<=0:continue
    assert potential.get(v,clip)<=potential.get(u,clip)+rc.increments[slot];checked+=1
  witnesses={}
  for target in targets:
   node=target;edges=[];seen=set()
   while node!=source:
    assert node not in seen;seen.add(node);node,slot=pred[node];edges.append(fields['edge_ids'][slot])
   edges.reverse();assert rc.path(source,target,edges)==dist[target]==potential.get(target,clip);witnesses[str(target)]=edges
  cert=D/f'w{width}_source{source}.json'
  with cert.open('x') as f:json.dump(dict(source=source,clip=clip,potentials=potential,witnesses=witnesses,scale=rc.scale,graph_sha256=digest),f,separators=(',',':'));f.write('\n')
  certs.append(dict(path=str(cert),sha256=sha(cert),inequalities=checked))
  for plan in group:
   minimum=F(dist[plan['query']['sink']]*10**9,rc.scale);limit=F(plan['budget_ns']);rows.append(dict(width=width,index=plan['index'],connection_id=plan['query']['connection_id'],minimum_ns=str(minimum),budget_ns=str(limit),classification='RELAXED_FLOOR_EXCEEDS_BUDGET' if minimum>limit else 'RELAXED_WITHIN_BUDGET_PATH_EXISTS'))
 print(width,'violations',len(selected),'over floor',sum(r['width']==width and r['classification']=='RELAXED_FLOOR_EXCEEDS_BUDGET' for r in rows),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,certificates=certs,total_seconds=time.perf_counter()-start,scope='All12 historical violations; exact integer clipped-potential all-edge lower-bound and attaining-path checks using existing authenticated RC loader. Not independently extracted XML RC, native shared-tree STA, joint feasibility or speed evidence.'),f,indent=2);f.write('\n')
