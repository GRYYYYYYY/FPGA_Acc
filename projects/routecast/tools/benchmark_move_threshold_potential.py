"""Actual consecutive placements: lower-bound endpoint-only cache hazards."""
import json,heapq,time,os
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from affected_connections import affected
from pre_route_endpoints import sha
from cost_read_dependency_index import CostReadDependencyIndex
from potential_occupancy_threshold import required_other_demand


def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments'
 sequence=base/'adder_tree_2L032_move_sequence_2026-10-06'
 audit=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 mode=os.environ['ROUTECAST_POTENTIAL_MODE'];assert mode in ('full','certificate');out=Path(os.environ['ROUTECAST_POTENTIAL_OUTPUT']);assert out.parent==base;out.mkdir()
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
 cache={};potentials={};thresholds={}
 incoming=defaultdict(list)
 for eid,(u,i) in slots.items():
  if f['costs'][i]!=(1<<64)-1 and f['capacities'][f['dest_ranks'][i]]>0:incoming[f['dest_ranks'][i]].append((u,i))
 def query(row,unions,occ):
  source,sink,net=row['source'],row['sink'],row['net_id'];dist={source:0};parent={};heap=[(0,source)];footprint=set();settled={}
  while heap:
   cost,node=heapq.heappop(heap)
   if dist.get(node)!=cost:continue
   if mode=='certificate':settled[node]=cost
   if node==sink:
    if mode=='certificate':potentials[row['connection_id']]=(dict(settled),cost);thresholds[row['connection_id']]={}
    path=[];current=sink
    while current!=source:
     previous,eid=parent[current];path.append(eid);current=previous
    path.reverse();return ('FOUND',cost,tuple(path)),footprint
   for i in range(f['row_offsets'][node],f['row_offsets'][node+1]):
    n=f['dest_ranks'][i];scalar=int(f['costs'][i])
    if scalar==(1<<64)-1 or f['capacities'][n]<=0:continue
    assert scalar>0
    other=occ[n]-(n in unions[net]);assert other>=0
    candidate=cost+scalar*(1+other)
    if candidate<dist.get(n,1<<256):
     dist[n]=candidate;parent[n]=(node,f['edge_ids'][i]);heapq.heappush(heap,(candidate,n))
  return ('UNREACHABLE',None,None),footprint
 au,ao=state(pred);start=time.monotonic()
 for row in endpoints['connections']:
  result,footprint=query(row,au,ao);cid=row['connection_id'];cache[cid]=(result,footprint);
 warm_s=time.monotonic()-start;reports=[]
 print(json.dumps({'warm_queries':len(cache),'mode':mode,'warm_s':warm_s}),flush=True)
 for step in sr['steps']:
  k=step['step'];assert all(sha(sequence/n)==h for n,h in step['outputs_sha256'].items())
  after=load(sequence/f'step_{k}_endpoints.json');new=load(audit/f'step_{k}_prediction.json');assert sha(audit/f'step_{k}_prediction.json')==ar['steps'][k-1]['prediction_sha256']
  golden_rows=load(base/'adder_tree_move_dynamic_cache_replay_2026-10-06'/f'step_{k}_queries.json');golden={r['connection_id']:r for r in golden_rows};start=time.monotonic()
  closure=affected(endpoints,after);endpoint_dirty=set(closure['recompute_connection_ids']);bu,bo=state(new)
  global_dirty={n for n in set(ao)|set(bo) if ao[n]!=bo[n]}
  conservative_count=0;cost_dirty=set()
  certified=set();edges_checked=0;threshold_hits=0;threshold_builds=0
  for row in (after['connections'] if mode=='certificate' else []):
   cid=row['connection_id'];net=row['net_id']
   if cid in endpoint_dirty:continue
   result=cache[cid][0]
   if result[0]!='FOUND':continue
   new_cost=sum(int(f['costs'][slots[e][1]])*(1+bo[f['dest_ranks'][slots[e][1]]]-(f['dest_ranks'][slots[e][1]] in bu[net])) for e in result[2])
   if new_cost!=result[1]:continue
   values,ceiling=potentials[cid];valid=True
   changed=global_dirty|(au[net]^bu[net])
   for n in changed:
    old_other=ao[n]-(n in au[net]);new_other=bo[n]-(n in bu[net])
    if new_other>=old_other:continue
    memo=thresholds[cid]
    if n not in memo:
     memo[n]=required_other_demand(values.get(n,ceiling),((values.get(u,ceiling),int(f['costs'][i])) for u,i in incoming[n]));edges_checked+=len(incoming[n]);threshold_builds+=1
    else:threshold_hits+=1
    if new_other<memo[n]:valid=False
    if not valid:break
   if valid:certified.add(cid)
  invalid={row['connection_id'] for row in after['connections']}-certified
  for cid in invalid:cache.pop(cid,None)
  hits=recomputed=path_differences=0;records=[]
  for row in after['connections']:
   cid=row['connection_id'];cached=cache.get(cid)
   if cached is None:
    result,footprint=query(row,bu,bo);cache[cid]=(result,footprint);recomputed+=1
   else:result=cached[0];hits+=1
   truth=golden[cid];assert result[:2]==(truth['status'],truth['cost']);path_differences+=result[2]!=tuple(truth['path'])
   if result[0]=='FOUND':
    node=row['source'];objective=0;seen={node}
    for eid in result[2]:
     u,i=slots[eid];assert u==node;node=f['dest_ranks'][i];assert node not in seen;seen.add(node)
     objective+=int(f['costs'][i])*(1+bo[node]-(node in bu[row['net_id']]))
    assert node==row['sink'] and objective==result[1]
   records.append({'connection_id':cid,'status':result[0],'cost':result[1],'path':result[2],'retained':cached is not None})
  step_s=time.monotonic()-start
  (out/f'step_{k}_queries.json').write_text(json.dumps(records)+'\n')
  report={'step':k,'endpoint_invalidated':len(endpoint_dirty),'conservative_cost_candidates':conservative_count,'cost_invalidated':len(cost_dirty),'combined_invalidated':len(invalid),'persistent_optimality_certified':len(certified),'certificate_edges_checked':edges_checked,'threshold_cache_hits':threshold_hits,'threshold_builds':threshold_builds,'equal_cost_path_differences':path_differences,'retained':hits,'recomputed':recomputed,'full_dynamic_status_cost_parity':True,'prepared_step_s':step_s,'queries_sha256':sha(out/f'step_{k}_queries.json')};reports.append(report);print(json.dumps(report),flush=True)
  endpoints,pred,au,ao=after,new,bu,bo
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'source.py').write_text(Path(__file__).read_text())
 (out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'mode':mode,'warm_s':warm_s,'threshold_source_sha256':sha(root/'tools/potential_occupancy_threshold.py'),'dependency_source_sha256':sha(root/'tools/cost_read_dependency_index.py'),'steps':reports,'scope':'Actual three consecutive moves and independently validated constant-predictor occupancy snapshots. Deterministic per-query positive scalar*(1+otherNET demand) Dijkstra; Diagnostic scalar optimality certificate: settled distances capped at sink cost define feasible potentials; only decreased demand requires a check; each node threshold lazily caches max(0,max_u ceil((p(v)-p(u))/scalar)-1), discarded on new potential, unchanged old path cost certifies optimality. Archived independently verified full status/cost checks and physical witness checks; no online oracle search. Equal-cost path identity counted separately, not assumed. Persistent retained result and feasible potential across all three transitions, no full-oracle state publication. Every unchanged-endpoint query must pass path cost and every decreased incoming-edge potential inequality regardless of stale cost-read footprints. Certificates prove optimal cost, not canonical tie path. Cost-read diagnostics removed for timing. Prepared timing includes initial search, per-query potential maintenance only in certificate mode; no footprint/reverse index maintenance in either mode, endpoint closure, certificate/recompute, and witness checks; excludes loading, conversion, output serialization and native. This scope does not establish overall native net benefit. Dynamic query paths do not update occupancy; no online dynamic routing ledger, RC budget, native gain or speedup. ABBA development search-state timing only.'},indent=2)+'\n')
if __name__=='__main__':main()
