"""Shortest-distance certificate via edge inequalities and predecessor trees."""
import json
from pathlib import Path
from fractions import Fraction
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_fullnet_forbidden_resource_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12 and r['protocol_sha256']==sha(out/'protocol.json');rows=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];d=json.loads(file.read_text());ctx=PersistentRCContext(d['target']);assert ctx.context[1]==d['graph_sha256'];f=ctx.rc.fields;inc=ctx.rc.increments;blocked=d['forbidden_rank'];assert int(ctx.context[2][blocked].get('id'))==d['physical_node_id'];slot_source={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';assert sha(af)==d['allocation_sha256'];allocation=json.loads(af.read_text());checked=0
 old=json.loads((ROOT/f'experiments/mux_forbidden_resource_v2_2026-10-06/w{w}_m{i}.json').read_text());assert old['forbidden_rank']==blocked and old['prediction_sha256']==d['prediction_sha256']
 represented={ans['query']['net_id'] for ans in d['answers']};assert represented=={ans['query']['net_id'] for ans in old['answers']};assert {ans['query']['connection_id'] for ans in d['answers']}=={q['connection_id'] for q in ctx.context[5] if q['net_id'] in represented}
 for ans in d['answers']:
  ans={**ans,**d['certificates'][ans['certificate_source']]}
  assert ans['query']==next(q for q in ctx.context[5] if q['connection_id']==ans['query']['connection_id'])
  source,sink=ans['query']['source'],ans['query']['sink'];dist={int(k):v for k,v in ans['distances'].items()};pred={int(k):v for k,v in ans['predecessor_slots'].items()};assert blocked not in dist
  if source==blocked:assert not dist
  else:assert dist[source]==0 and set(pred)==set(dist)-{source}
  for u,value in dist.items():
   assert value>=0
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if v==blocked or f['capacities'][v]<=0:continue
    assert v in dist and dist[v]<=value+inc[s]
  resolved={source} if source in dist else set()
  for v in pred:
   trail=[];seen=set();n=v
   while n not in resolved:
    assert n not in seen;seen.add(n);trail.append(n);s=pred[n];u=slot_source[s];assert f['dest_ranks'][s]==n and u in dist and dist[n]==dist[u]+inc[s];n=u
   resolved.update(trail)
  assert ans['minimum']==dist.get(sink)
  limit=min(int(Fraction(allocation['budgets_ns'][str(ans['query']['connection_id'])])*ctx.rc.scale/10**9),ctx.rc.scale//10**9);assert ans['budget']==limit and ans['within_budget']==(sink in dist and dist[sink]<=limit);checked+=len(dist)
 rows.append(dict(width=w,index=i,queries=len(d['answers']),finite_labels_checked=checked,within_budget=sum(x['within_budget'] for x in d['answers'])))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent certificate: every traversable edge inequality and exact predecessor-root witness. Complete integer shortest-delay model with forbidden rank; shared authenticated RC increment loader, not independent original XML/Fraction delay proof or global STA/capacity proof.'),indent=2)+'\n');print(rows)
