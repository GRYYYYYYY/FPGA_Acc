"""XML ownership reconstruction and independent shortest-distance certificates."""
import json
from collections import defaultdict,Counter
from pathlib import Path
from fractions import Fraction as F
from persistent_rc_context import PersistentRCContext
from immutable_xml_prediction_audit import ImmutableXMLAudit
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_residual_failure_2026-10-06';parent=ROOT/'experiments/mux_capacity_avoid_reroute_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12;rows=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];d=json.loads(file.read_text());pf=parent/f'w{w}_m{i}/prediction.json';assert sha(pf)==d['prediction_sha256'];p=json.loads(pf.read_text());q=d['query'];assert p['failure']['query']==q==p['events'][-1]['query'] and not p['events'][-1]['committed'];ctx=PersistentRCContext(d['target']);assert q in ctx.context[5] and ctx.context[1]==d['graph_sha256'];f=ctx.rc.fields;inc=ctx.rc.increments;xml=ImmutableXMLAudit(ctx.context[0],d['graph_sha256']);unions=defaultdict(set)
 for rec in p['records']:
  unions[rec['net_id']].add(rec['source'])
  for eid in rec['answer']['physical_edge_ids']:e=xml.graph.edges[eid];unions[rec['net_id']].update((e.source,e.sink))
 ledger=Counter(n for union in unions.values() for n in union);assert ledger==Counter({int(n):c for n,c in p['ledger'].items()});other={n:c-int(n in unions[q['net_id']]) for n,c in ledger.items()};assert {n:c for n,c in other.items() if c}=={int(n):c for n,c in d['other'].items()}
 af=ROOT/f'experiments/mux_capacity_budgets_2026-10-06/w{w}_m{i}.json';assert sha(af)==d['allocation_sha256'];a=json.loads(af.read_text());pairs={(x['source'],x['sink']) for x in ctx.context[5] if x['net_id']==a['selected_net']};restriction={a['forbidden_rank']} if (q['source'],q['sink']) in pairs else set();assert sorted(restriction)==d['restriction'];budget=min(int(F(a['budgets_ns'][str(q['connection_id'])])*ctx.rc.scale/10**9),ctx.rc.scale//10**9);assert budget==d['budget'];slot_source={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};labels=0
 for mode,cert in d['certificates'].items():
  blocked=restriction|({n for n,c in other.items() if c>=xml.caps[n]} if mode=='residual' else set());assert blocked==set(cert['blocked']);dist={int(n):v for n,v in cert['distances'].items()};pred={int(n):s for n,s in cert['predecessor_slots'].items()};source=q['source'];assert not blocked.intersection(dist)
  if source in blocked:assert not dist
  else:assert dist[source]==0 and set(pred)==set(dist)-{source}
  for u,value in dist.items():
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if v in blocked or xml.caps[v]<=0:continue
    assert v in dist and dist[v]<=value+inc[s]
  rooted={source} if source in dist else set()
  for n in pred:
   trail=[];seen=set()
   while n not in rooted:
    assert n not in seen;seen.add(n);trail.append(n);s=pred[n];u=slot_source[s];assert f['dest_ranks'][s]==n and dist[n]==dist[u]+inc[s];n=u
   rooted.update(trail)
  assert cert['minimum']==dist.get(q['sink']) and cert['within_budget']==(q['sink'] in dist and dist[q['sink']]<=budget);labels+=len(dist)
  path=[];n=q['sink']
  if n in dist:
   while n!=source:path.append(n);n=slot_source[pred[n]]
   path.append(n);path.reverse()
  assert path==cert['path_nodes']
 expected=[dict(node=n,owners=sorted(net for net,union in unions.items() if net!=q['net_id'] and n in union)) for n in d['certificates']['relaxed']['path_nodes'] if other.get(n,0)>=xml.caps[n]];assert expected==d['relaxed_witness_blockers'];rows.append(dict(width=w,index=i,finite_labels_checked=labels,relaxed_within_budget=d['certificates']['relaxed']['within_budget'],residual_within_budget=d['certificates']['residual']['within_budget']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Original XML ownership/demand reconstruction plus exact integer edge/predecessor shortest-delay certificates. Shared RC increments; not independent Fraction or native STA. Relaxed witness owner observations do not certify a minimal blocking set.'),indent=2)+'\n');print(rows)
