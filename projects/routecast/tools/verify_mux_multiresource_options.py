"""Exclusion provenance, exhaustive NET coverage and shortest-label certificates."""
import json
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_multiresource_options_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12;rows=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];d=json.loads(file.read_text());rf=ROOT/f'experiments/mux_residual_failure_2026-10-06/w{w}_m{i}.json';af=ROOT/f'experiments/mux_capacity_budgets_2026-10-06/w{w}_m{i}.json';assert sha(rf)==d['residual_sha256'] and sha(af)==d['allocation_sha256'];old=json.loads(af.read_text());res=json.loads(rf.read_text());block=res['relaxed_witness_blockers'][0];assert d['new_resource']==block['node'];assert {o['chosen_net'] for o in d['options']}=={res['query']['net_id'],*block['owners']};ctx=PersistentRCContext(d['target']);assert ctx.context[1]==d['graph_sha256'] and ctx.rc.scale==d['scale'];f=ctx.rc.fields;inc=ctx.rc.increments;queries={q['connection_id']:q for q in ctx.context[5]};sources={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};labels=0;count=0
 for option in d['options']:
  restriction={old['selected_net']:{old['forbidden_rank']}};restriction.setdefault(option['chosen_net'],set()).add(block['node']);assert {int(n):set(v) for n,v in option['restrictions'].items()}==restriction
  assert {a['query']['connection_id'] for a in option['answers']}=={cid for cid,q in queries.items() if q['net_id'] in restriction}
  for cert in option['certificates'].values():
   banned=set(cert['forbidden']);source=cert['source'];dist={int(n):v for n,v in cert['distances'].items()};pred={int(n):s for n,s in cert['predecessor_slots'].items()};assert not banned.intersection(dist)
   if source in banned:assert not dist
   else:assert dist[source]==0 and set(pred)==set(dist)-{source}
   for u,value in dist.items():
    for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     v=f['dest_ranks'][slot]
     if v in banned or f['capacities'][v]<=0:continue
     assert v in dist and dist[v]<=value+inc[slot]
   rooted={source} if source in dist else set()
   for n in pred:
    seen=set();trail=[]
    while n not in rooted:
     assert n not in seen;seen.add(n);trail.append(n);s=pred[n];u=sources[s];assert f['dest_ranks'][s]==n and dist[n]==dist[u]+inc[s];n=u
    rooted.update(trail)
   labels+=len(dist)
  for ans in option['answers']:
   q=ans['query'];assert q==queries[q['connection_id']];cert=option['certificates'][ans['certificate']];assert cert['source']==q['source'] and set(cert['forbidden'])==restriction[q['net_id']];assert ans['minimum']==cert['distances'].get(str(q['sink']));count+=1
 rows.append(dict(width=w,index=i,options=len(d['options']),queries=count,certificate_labels=labels))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Exact integer minimum certificates, target NET completeness and old/new restriction provenance. Shared RC increment loader; no full DAG feasibility, capacity realization or native STA guarantee.'),indent=2)+'\n');print(rows)
