"""Actual consecutive placements: lower-bound endpoint-only cache hazards."""
import json,heapq,time
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from affected_connections import affected
from pre_route_endpoints import sha
from cost_read_dependency_index import CostReadDependencyIndex


def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments'
 sequence=base/'adder_tree_2L032_move_sequence_2026-10-06'
 audit=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 out=base/'adder_tree_move_dynamic_cache_replay_2026-10-06';out.mkdir()
 bindings={}
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 sr=load(sequence/'receipt.json');ar=load(audit/'receipt.json')
 endpoints=load(base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json')
 pred=load(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json')
 br=load(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/receipt.json');assert sha(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json')==br['prediction_sha256']
 m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',endpoints['graph_sha256'])
 slots={f['edge_ids'][i]:(u,i) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 def state(p):
  unions=defaultdict(set)
  for r in p['connections']:
   unions[r['net_id']].add(r['source'])
   for e in r['physical_edge_ids']:
    u,i=slots[e];unions[r['net_id']].update((u,f['dest_ranks'][i]))
  occ=Counter(n for nodes in unions.values() for n in nodes)
  assert +occ==Counter({int(n):v for n,v in p['node_occupancy'].items()})
  return unions,occ
 index=CostReadDependencyIndex(endpoints['graph_sha256']);cache={}
 def query(row,unions,occ):
  source,sink,net=row['source'],row['sink'],row['net_id'];dist={source:0};parent={};heap=[(0,source)];footprint=set()
  while heap:
   cost,node=heapq.heappop(heap)
   if dist.get(node)!=cost:continue
   if node==sink:
    path=[];current=sink
    while current!=source:
     previous,eid=parent[current];path.append(eid);current=previous
    path.reverse();return ('FOUND',cost,tuple(path)),footprint
   for i in range(f['row_offsets'][node],f['row_offsets'][node+1]):
    n=f['dest_ranks'][i];scalar=int(f['costs'][i])
    if scalar==(1<<64)-1 or f['capacities'][n]<=0:continue
    assert scalar>0
    footprint.add(n);other=occ[n]-(n in unions[net]);assert other>=0
    candidate=cost+scalar*(1+other)
    if candidate<dist.get(n,1<<256):
     dist[n]=candidate;parent[n]=(node,f['edge_ids'][i]);heapq.heappush(heap,(candidate,n))
  return ('UNREACHABLE',None,None),footprint
 au,ao=state(pred);start=time.monotonic()
 for row in endpoints['connections']:
  result,footprint=query(row,au,ao);cid=row['connection_id'];cache[cid]=(result,footprint);index.register(cid,row['net_id'],footprint)
 warm_s=time.monotonic()-start;reports=[]
 print(json.dumps({'warm_queries':len(cache),'warm_s':warm_s}),flush=True)
 for step in sr['steps']:
  start=time.monotonic();k=step['step'];assert all(sha(sequence/n)==h for n,h in step['outputs_sha256'].items())
  after=load(sequence/f'step_{k}_endpoints.json');new=load(audit/f'step_{k}_prediction.json');assert sha(audit/f'step_{k}_prediction.json')==ar['steps'][k-1]['prediction_sha256']
  closure=affected(endpoints,after);endpoint_dirty=set(closure['recompute_connection_ids']);bu,bo=state(new)
  global_dirty={n for n in set(ao)|set(bo) if ao[n]!=bo[n]}
  cost_dirty=set()
  # Global changes plus per-owner union changes safely cover otherNET changes.
  for n in global_dirty:cost_dirty.update(index.readers.get(n,()))
  for cid,(owner,footprint) in index.entries.items():
   if footprint & (au[owner]^bu[owner]):cost_dirty.add(cid)
  invalid=endpoint_dirty|cost_dirty
  for cid in invalid:index.discard(cid);cache.pop(cid,None)
  hits=recomputed=0;records=[]
  for row in after['connections']:
   cid=row['connection_id'];cached=cache.get(cid)
   if cached is None:
    result,footprint=query(row,bu,bo);cache[cid]=(result,footprint);index.register(cid,row['net_id'],footprint);recomputed+=1
   else:result=cached[0];hits+=1
   full,_=query(row,bu,bo);assert result==full
   if result[0]=='FOUND':
    node=row['source'];objective=0;seen={node}
    for eid in result[2]:
     u,i=slots[eid];assert u==node;node=f['dest_ranks'][i];assert node not in seen;seen.add(node)
     objective+=int(f['costs'][i])*(1+bo[node]-(node in bu[row['net_id']]))
    assert node==row['sink'] and objective==result[1]
   records.append({'connection_id':cid,'status':result[0],'cost':result[1],'path':result[2],'retained':cached is not None})
  (out/f'step_{k}_queries.json').write_text(json.dumps(records)+'\n')
  report={'step':k,'endpoint_invalidated':len(endpoint_dirty),'cost_invalidated':len(cost_dirty),'combined_invalidated':len(invalid),'retained':hits,'recomputed':recomputed,'full_dynamic_query_parity':True,'wall_including_full_oracle_s':time.monotonic()-start,'queries_sha256':sha(out/f'step_{k}_queries.json')};reports.append(report);print(json.dumps(report),flush=True)
  endpoints,pred,au,ao=after,new,bu,bo
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'source.py').write_text(Path(__file__).read_text())
 (out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'warm_s':warm_s,'dependency_source_sha256':sha(root/'tools/cost_read_dependency_index.py'),'steps':reports,'scope':'Actual three consecutive moves and independently validated constant-predictor occupancy snapshots. Deterministic per-query positive scalar*(1+otherNET demand) Dijkstra; endpoint closure and conservative cost-read invalidation, fresh full query and physical/objective witness parity. Dynamic query paths do not update occupancy; no online dynamic routing ledger, RC budget, native gain or speedup. Initialization and full oracle times are diagnostic.'},indent=2)+'\n')
if __name__=='__main__':main()
