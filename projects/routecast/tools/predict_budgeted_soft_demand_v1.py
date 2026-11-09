"""Endpoint-only shared rooted RC trees; overuse is measured demand, not a legal route."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints

def predict(endpoint,floorfile,output):
 begin=time.perf_counter();endpoint=Path(endpoint).resolve();floorfile=Path(floorfile).resolve();out=Path(output).resolve();out.mkdir();bindings={**closure([Path(__file__)]),str(endpoint):sha(endpoint),str(floorfile):sha(floorfile)};bindings.update({v['path']:v['sha256'] for v in json.loads(endpoint.read_text())['inputs'].values()});graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(floorfile.read_text())};groups=defaultdict(list)
 for q in queries:groups[q['net_id']].append(q)
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='Endpoint-only original additive RC budget shortest rooted single-parent tree per NET. Positive-capacity physical graph; no cross-NET hard-cap rejection. Report unique-NET demand and explicit capacity overflow; not a legal joint route or checkpoint. Counting ablation uses the exact same paths but independent connection charge. No native labels in prediction inputs; full original endpoint scope.',required_connections=len(queries)),indent=2)+'\n');records=[];owners={};independent=Counter();failures=[]
 for net,qs in sorted(groups.items()):
  assert len({q['source'] for q in qs})==1;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;d=[cap]*len(nodes);d[src]=min(cap,rc.initial(src));queue=[(d[src],src)] if f['capacities'][src]>0 and d[src]<cap else [];parents={}
  while queue:
   delay,u=heapq.heappop(queue)
   if delay!=d[u]:continue
   for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][e]
    if f['capacities'][v]<=0:continue
    cost=min(cap,delay+rc.increments[e])
    if cost<d[v]:d[v]=cost;parents[v]=(u,e);heapq.heappush(queue,(cost,v))
  owned=set()
  for q in sorted(qs,key=lambda q:q['connection_id']):
   if d[q['sink']]>budgets[q['connection_id']]:failures.append(dict(query=q,status='BUDGET_UNREACHABLE'));continue
   u=q['sink'];path=[];used={u}
   while u!=src:
    previous,e=parents[u];path.append(f['edge_ids'][e]);u=previous;assert u not in used;used.add(u)
   path.reverse();assert rc.path(src,q['sink'],path)==d[q['sink']];owned.update(used);independent.update(used);records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budgets[q['connection_id']],floor_integer=floors[src,q['sink']]))
  owners[net]=owned
 ledger=Counter(n for owned in owners.values() for n in owned);overflow=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());candidate=dict(status='COMPLETE_DEMAND_SKETCH' if not failures else 'INCOMPLETE_DEMAND_SKETCH',records=records,ledger=dict(ledger),independent_connection_ledger=dict(independent),completed_connections=len(records),required_connections=len(queries),failure=failures[0] if failures else None,failures=failures,overflow_units=overflow,overflow_nodes=sum(c>f['capacities'][n] for n,c in ledger.items()),eligible_for_legal_route_commit=False,graph_sha256=digest,scope='Complete endpoint demand estimate with possible cross-NET overuse; no route acceptance.')
 (out/'sketch.json').write_text(json.dumps(candidate)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,total_paid_prediction_seconds=time.perf_counter()-begin,completed=len(records),required=len(queries),overflow_units=overflow,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');return {k:candidate[k] for k in ('status','completed_connections','required_connections','overflow_units','overflow_nodes')}
if __name__=='__main__':print(json.dumps(predict(*sys.argv[1:])),flush=True)
