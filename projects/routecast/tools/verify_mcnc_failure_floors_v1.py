"""Independent reverse exact minimum and a diagnostic retained-prefix splice."""
import json,sys,heapq
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from source_binding_v2 import closure
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_first_failure_diagnosis_v3_2026-10-07';receipt=out/'receipt.json';r=json.loads(receipt.read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(receipt):sha(receipt)};assert all(sha(path)==h for path,h in bindings.items());(out/'reverse_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Post-outcome reverse scalar Dijkstra optimum parity, witness replay and diagnostic same-NET retained-prefix splice only; no original predictor retuning or native QoR acceptance.'),indent=2)+'\n');verified=[]
for row in r['rows']:
 w=base/row['name'];c=json.loads((w/'candidate.json').read_text());q=row['query'];graph,digest,nodes,f,rc,queries=load_endpoints(w/'endpoints.json');reverse=[[] for _ in nodes];eid_slot={eid:s for s,eid in enumerate(f['edge_ids'])};edge_source={}
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s));edge_source[f['edge_ids'][s]]=u
 owners=defaultdict(set);parents={}
 for rec in c['records']:
  owners[rec['net_id']].add(rec['source'])
  for eid in rec['answer']['physical_edge_ids']:
   v=f['dest_ranks'][eid_slot[eid]];owners[rec['net_id']].add(v)
   if rec['net_id']==q['net_id']:parents[v]=(edge_source[eid],eid)
 other=Counter(n for net,ns in owners.items() if net!=q['net_id'] for n in ns);floors={}
 for mode,blocked in [('unrestricted',{}),('other_net_conditioned',other)]:
  allowed=lambda n:f['capacities'][n]>blocked.get(n,0);dist={};queue=[]
  if allowed(q['sink']):dist[q['sink']]=0;queue=[(0,q['sink'])]
  while queue:
   d,v=heapq.heappop(queue)
   if d!=dist[v]:continue
   if v==q['source']:break
   for u,s in reverse[v]:
    if not allowed(u):continue
    nd=d+rc.increments[s]
    if u not in dist or nd<dist[u]:dist[u]=nd;heapq.heappush(queue,(nd,u))
  minimum=rc.initial(q['source'])+dist[q['source']] if q['source'] in dist else None;expected=row['floors'][mode];assert minimum==expected['minimum_integer'];floors[mode]=minimum
  if minimum is not None:
   assert rc.path(q['source'],q['sink'],expected['edge_ids'])==minimum
   assert all(allowed(n) for n in [q['source']]+[f['dest_ranks'][eid_slot[e]] for e in expected['edge_ids']])
 splice=None
 if row['tree_conflicts']:
  assert len(row['tree_conflicts'])==1;event=next(e for e in reversed(c.get('events',c.get('attempts',[]))) if e.get('type','QUERY')=='QUERY' and e['query']==q);answer=event.get('answer',event.get('native_answer'));old=answer['physical_edge_ids'];join=row['tree_conflicts'][0]['node'];prefix=[];node=join;seen={node}
  while node!=q['source']:
   u,eid=parents[node];assert u not in seen;seen.add(u);prefix.append(eid);node=u
  prefix.reverse();idx=next(i for i,eid in enumerate(old) if f['dest_ranks'][eid_slot[eid]]==join);path=prefix+old[idx+1:];delay=rc.path(q['source'],q['sink'],path);newnodes={q['source']};conflicts=[]
  for eid in path:
   v=f['dest_ranks'][eid_slot[eid]];incoming=(edge_source[eid],eid);newnodes.add(v)
   if v in parents and parents[v]!=incoming:conflicts.append(v)
  assert not conflicts and all(other.get(n,0)<f['capacities'][n] for n in newnodes)
  splice=dict(join_node=join,edge_ids=path,delay_integer=delay,delay_ns=str(Fraction(delay*10**9,rc.scale)),within_original_budget=delay<=row['budget_integer'],single_parent_compatible=True,other_net_capacity_compatible=True,scope='Uncommitted post-outcome individual connection splice; not complete NET routing/native pin/STA proof. Retained own union not released.')
 verified.append(dict(name=row['name'],reverse_minima_equal_forward=floors,splice=splice));print('PASS',row['name'],splice['delay_ns'] if splice else None,flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'reverse_verification.json').write_text(json.dumps(dict(rows=verified,bindings=bindings,all_reverse_minima_and_witnesses_pass=True),indent=2)+'\n')
