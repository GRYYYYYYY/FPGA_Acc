"""All single-extra-owner alternatives under unchanged four-owner cap."""
import json,sys,heapq,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/mcnc_bounded_owner_joint_v8_2026-10-07';base=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3';out=R/'experiments/misex_owner_limit_alternatives_v1_2026-10-07';out.mkdir();eventfile=parent/'misex3/batch7.json';ep=base/'endpoints.json';inputs={str(p):sha(p) for p in (eventfile,ep,parent/'receipt.json')};inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,policy='All existing kept owners, ordered by complete connection count then NET, one extra release; each failed child query retains forbidden node and original budget. Forward Dijkstra with budget cutoff, independent reverse counterpart. No joint commit, no maxowner relaxation.',scope='Development exhaustive single-extra-owner path feasibility, not complete joint routing or native/global proof.'))+'\n');begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads(eventfile.read_text());attempt=event['repair_attempts'][0];release=set(attempt['released_net_ids']);assert len(release)==3;kept=[r for r in event['before_records'] if r['net_id'] not in release];owners=defaultdict(set);counts=Counter(r['net_id'] for r in kept);slots={e:s for s,e in enumerate(f['edge_ids'])}
for r in kept:owners[r['net_id']].add(r['source']);owners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
rows=[]
for branch in attempt['branches']:
 for netstr,failure in branch['failures'].items():
  if failure is None:continue
  q=failure['query'];budget=failure['budget_integer'];forbidden={n for net,n in branch['constraints'] if net==q['net_id']};other=Counter(n for net,own in owners.items() if net!=q['net_id'] for n in own);tests=[]
  for extra in [None]+sorted((net for net in owners if net!=q['net_id']),key=lambda net:(counts[net],net)):
   blocked=other.copy()
   if extra is not None:blocked.subtract(owners[extra])
   allowed=lambda n:n not in forbidden and f['capacities'][n]>blocked[n];results=[];path=None
   for backward in (False,True):
    src,sink=q['source'],q['sink'];root=sink if backward else src;target=src if backward else sink;initial=0 if backward else rc.initial(src);dist={root:initial} if allowed(root) and allowed(target) else {};heap=[(d,u) for u,d in dist.items()];back={};answer=None
    while heap:
     d,u=heapq.heappop(heap)
     if d!=dist[u]:continue
     if d+(rc.initial(src) if backward else 0)>budget:break
     if u==target:answer=d+(rc.initial(src) if backward else 0);break
     arcs=reverse[u] if backward else ((f['dest_ranks'][s],s) for s in range(f['row_offsets'][u],f['row_offsets'][u+1]))
     for v,s in arcs:
      if not allowed(v):continue
      nd=d+rc.increments[s]
      if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
    results.append(answer)
    if not backward and answer is not None:
     path=[];v=sink
     while v!=src:v,e=back[v];path.append(e)
     path.reverse();assert rc.path(src,sink,path)==answer
   assert results[0]==results[1];tests.append(dict(extra_net=extra,removed_connection_count=0 if extra is None else counts[extra],minimum_within_budget_integer=results[0],physical_edge_ids=path,forward_reverse_equal=True))
  rows.append(dict(query=q,budget_integer=budget,forbidden_nodes=sorted(forbidden),candidates=tests));print(q['net_id'],'tested',len(tests),'feasible',[(x['extra_net'],x['minimum_within_budget_integer']) for x in tests if x['minimum_within_budget_integer'] is not None],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),initial_release=sorted(release),max_owner_nets=4,total_seconds=time.perf_counter()-begin,rows=rows,scope='Null means no path within budget under that condition, not necessarily unreachable.'),indent=2)+'\n')
