"""Independent forward Dijkstra and owner-union replay for conditioned perNET floors."""
import json,sys,heapq,time
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);out=ROOT/f'experiments/native_resume_conditional_rr_floors_w{w}_m{i}_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and all(sha(f)==h for f,h in p['inputs'].items());start=time.perf_counter()
ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';_,_,nodes,f,rc,queries=load_endpoints(ep);assert rc.scale==r['scale'];meta=json.loads(ep.read_text());byid={q['connection_id']:q for q in queries};route=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07/canonical/design.route';paths=physical_paths(route);owners={name:{n for ps in seq for n,sw in ps} for name,seq in paths.items() if seq};occ=Counter(n for union in owners.values() for n in union);arc={f['edge_ids'][s]:(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};rows=[]
for index,row in enumerate(r['rows']):
 name=row['net'];other=Counter(occ);other.subtract(owners[name]);assert {str(n):v for n,v in other.items() if v}==row['other_occupancy'];qs=[x['query'] for x in row['records']];source=qs[0]['source'];assert all(q['source']==source and q==byid[q['connection_id']] and meta['net_names'][str(q['net_id'])]==name for q in qs)
 pending={q['sink'] for q in qs};dist={source:rc.initial(source)};heap=[(dist[source],source)];done=set()
 while heap and pending:
  value,u=heapq.heappop(heap)
  if u in done or value!=dist[u]:continue
  done.add(u);pending.discard(u)
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if other.get(v,0)>=f['capacities'][v]:continue
   proposed=value+rc.increments[s]
   if proposed<dist.get(v,proposed+1):dist[v]=proposed;heapq.heappush(heap,(proposed,v))
 assert not pending
 union=set();parent={}
 for x in row['records']:
  q=x['query'];assert x['conditional_integer']==dist[q['sink']]>=x['unconditional_integer'];assert rc.path(q['source'],q['sink'],x['physical_edge_ids'])==dist[q['sink']]
  u=q['source'];union.add(u)
  for eid in x['physical_edge_ids']:
   previous,v,switch=arc[eid];assert previous==u and other.get(v,0)<f['capacities'][v]
   if v in parent:assert parent[v]==(u,switch)
   parent[v]=u,switch;union.add(v);u=v
  assert u==q['sink']
 assert sorted(union)==row['new_union'] and all(other.get(n,0)+1<=f['capacities'][n] for n in union)
 assert sha(out/f'net_{index}.bin')==row['payload_sha256'] and sha(out/f'net_{index}.jsonl')==row['output_sha256']
 rows.append(dict(net=name,connections=len(qs),independent_minimum_matches=True,consistent_tree_and_frozen_other_capacity=True))
combined=Counter(occ)
for row in r['rows']:combined.subtract(owners[row['net']]);combined.update(row['new_union'])
overflow={str(n):v-f['capacities'][n] for n,v in combined.items() if v>f['capacities'][n]}
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,simultaneous_replacement_overflow=overflow,verification_seconds=time.perf_counter()-start,scope='Independent Python integer Dijkstra vs compiled query, frozen owner replay, every new tree arc and capacity verified. Shared electrical loader; no native pin/configurable/loaded-tree STA acceptance. Combined replacement overflow evaluated separately; no commit.'),indent=2)+'\n');print(w,'verified',rows,'combined overflow units',sum(overflow.values()),flush=True)
