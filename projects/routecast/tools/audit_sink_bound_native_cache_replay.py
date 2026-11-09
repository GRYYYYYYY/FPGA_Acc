"""Replay actual endogenous NET epochs; test conservative exact-context reuse."""
import json,shutil,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from prepared_csr import read,U64
from csr_integer_budget_search import query
from csr_integer_sink_bound_search import query as pruned_query
from rc_feasible_cost_region import RCFeasibleCostRegion
from native_integer_rc_sink_bound import NativeIntegerRCSinkBound
from rc_read_dependency_cache import RCReadDependencyCache
from native_integer_rc_sink_bound_trace import NativeIntegerRCSinkBoundTrace
from prepared_rc_sink_bounds import PreparedRCSinkBounds
from native_integer_rc_search import NativeIntegerRC
from native_integer_rc_trace import NativeIntegerRCTrace
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments';prior=base/'adder_tree_online_rc_budget_net_sequence_v2_2026-10-06';out=base/'adder_tree_sink_bound_native_cache_replay_2026-10-06';out.mkdir();bindings={}
 def load(p):
  bindings[str(p)]=sha(p);return json.loads(p.read_text())
 receipt=load(prior/'receipt.json');verification=load(prior/'verification.json');assert sha(prior/'receipt.json')==verification['receipt_sha256']
 for folder in ('adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr','adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits'):
  for p in (base/folder).rglob('*'):
   if p.is_file():bindings[str(p)]=sha(p)
 initial=load(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json');manifest,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',initial['physical_graph_sha256'])
 slots={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['costs'][i]) for u in range(manifest['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 relevant={v for u,v,c in slots.values() if c!=U64 and c>0 and f['capacities'][v]>0}
 def union(rows):
  result=set()
  for r in rows:
   result.add(r['source'])
   for eid in r['physical_edge_ids']:result.update(slots[eid][:2])
  return result
 active={r['connection_id']:r for r in initial['connections']};previous={};reports=[]
 for step in range(4):
  endpoints=load(base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else base/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json')
  budgetrows=load(base/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json');budget={r['connection_id']:r['scaled_integer_budget'] for r in budgetrows}
  ref=load(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if step==0 else base/f'adder_tree_2L032_move_sequence_audit_2026-10-06/step_{step}_prediction.json');reference={r['connection_id']:r for r in ref['connections']}
  # Use authoritative replay's repaired NET list derived from changed endpoints
  # and exact delay, rather than infer repairs from occupancy differences.
  from integer_rc_context import IntegerRC
  from csr_exact_buffered_rc import ExactBufferedRC
  from buffered_rc_context import load as loadrc
  if step==0:
   rc=IntegerRC(ExactBufferedRC(f,*loadrc(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits',initial['physical_graph_sha256'])))
   native=NativeIntegerRC(rc);tracer=NativeIntegerRCTrace(rc);bound_native=NativeIntegerRCSinkBound(rc);pruned_cache=RCReadDependencyCache(manifest["nodes"])
   bounds=PreparedRCSinkBounds(base/'adder_tree_prepared_rc_sink_bounds_2026-10-06','dadcaee7761667b995ab9b37b6fa15b00529dddc8af7fd61ebdf13a9ab19d167',initial['physical_graph_sha256'],rc.scale,manifest['nodes']);cached_native=NativeIntegerRCSinkBoundTrace(rc,bounds)
   for p in (root/'tools/native_integer_rc_sink_bound_trace.py',root/'tools/native_integer_rc_prepared_sink_bound.py',root/'tools/prepared_rc_sink_bounds.py',root/'tools/rc_budget_native_sink_bound_trace/search.cpp',root/'build/rc_budget_native_sink_bound_trace_2026-10-06/search.so',base/'adder_tree_prepared_rc_sink_bounds_2026-10-06/receipt.json'):bindings[str(p)]=sha(p)
   for p in (base/'adder_tree_prepared_rc_sink_bounds_2026-10-06').glob('*.bin'):bindings[str(p)]=sha(p)
   bindings[str(root/"tools/rc_read_dependency_cache.py")]=sha(root/"tools/rc_read_dependency_cache.py")
   for p in (root/'tools/native_integer_rc_sink_bound.py',root/'tools/native_integer_rc_delta_search.py',root/'tools/rc_budget_native_sink_bound/search.cpp',root/'build/rc_budget_native_sink_bound_2026-10-06/search.so'):bindings[str(p)]=sha(p)
   region=RCFeasibleCostRegion(manifest['nodes'],[(u,f['dest_ranks'][i],rc.increments[i],f['costs'][i]) for u in range(manifest['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0])
   for p in (root/'tools/csr_integer_sink_bound_search.py',root/'tools/rc_feasible_cost_region.py'):bindings[str(p)]=sha(p)
   for p in (root/'tools/native_integer_rc_trace.py',root/'tools/rc_budget_native_trace/search.cpp',root/'build/rc_budget_native_trace_2026-10-06/search.so',root/'build/rc_budget_native_trace_2026-10-06/receipt.json'):bindings[str(p)]=sha(p)
   for p in (root/'build/rc_budget_native_2026-10-06/search.so',root/'tools/rc_budget_native/search.cpp',root/'tools/native_integer_rc_search.py',root/'tools/csr_integer_budget_search.py'):bindings[str(p)]=sha(p)
  if step==0:pruned_context=hashlib.sha256(json.dumps(bindings,sort_keys=True).encode()).hexdigest()
  groups=defaultdict(list)
  for row in endpoints['connections']:groups[row['net_id']].append(row)
  repaired=0
  for net,rows in sorted(groups.items()):
   if any(any(active[r['connection_id']][k]!=r[k] for k in ('net_id','source','sink')) or rc.path(r['source'],r['sink'],active[r['connection_id']]['physical_edge_ids'])>budget[r['connection_id']] for r in rows):
    repaired+=1
    for r in rows:active[r['connection_id']]=reference[r['connection_id']]
  assert repaired==receipt['steps'][step]['restored_same_layout_baseline_nets']
  unions={n:union([active[r['connection_id']] for r in rows]) for n,rows in groups.items()};occ=Counter(n for nodes in unions.values() for n in nodes)
  journal=load(prior/f'step_{step}_journal.json');assert sha(prior/f'step_{step}_journal.json')==receipt['steps'][step]['journal_sha256']
  counts=Counter({k:0 for k in ('queries','endpoint_unchanged','endpoint_budget_unchanged','endpoint_only_false_reuse','exact_context_reusable')})
  for entry in journal:
   net=entry['net_id'];other=occ.copy();other.subtract(unions[net]);signature={n:v for n,v in other.items() if v and n in relevant};results={r['connection_id']:r for r in entry['connections']};native.set_other(other);tracer.set_other(other);bound_native.set_other(other);cached_native.set_other(other)
   for row in groups[net]:
    footprint=set()
    def cost(u,i):
     v=f['dest_ranks'][i]
     if f['costs'][i]>0:footprint.add(v)
     return f['costs'][i]*(1+other[v])
    trace=query(rc,row['source'],row['sink'],budget[row['connection_id']],lambda u,i:f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,cost,10000)
    assert trace==native.query(row['source'],row['sink'],budget[row['connection_id']],10000)
    remaining=region.distance(row['sink'],True)
    pruned_reads=set()
    def pruned_cost(u,i):
     v=f['dest_ranks'][i]
     if f['costs'][i]>0:pruned_reads.add(v)
     return f['costs'][i]*(1+other[v])
    pruned=pruned_query(rc,row['source'],row['sink'],budget[row['connection_id']],lambda u,i:f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,pruned_cost,remaining,10000)
    assert pruned==bound_native.query_bound(row['source'],row['sink'],budget[row['connection_id']],remaining,10000)
    assert all(pruned[k]==trace[k] for k in ('status','cost','delay','physical_edge_ids'))
    pruned_key=hashlib.sha256(json.dumps((pruned_context,row['net_id'],row['source'],row['sink'],budget[row['connection_id']],10000,'SINK_BOUND_V1')).encode()).hexdigest()
    reused=pruned_cache.lookup(row['connection_id'],pruned_key,other)
    if reused is not None:
     actual,native_reads=reused;counts['pruned_full_result_reusable']+=1;counts['actual_searches_skipped']+=1
    else:
     actual,native_reads=cached_native.traced_query(row['source'],row['sink'],budget[row['connection_id']],10000);pruned_cache.store(row['connection_id'],pruned_key,other,native_reads,actual);counts['native_trace_searches_executed']+=1
    assert actual==pruned and native_reads==frozenset(pruned_reads)
    counts['original_read_nodes']+=len(footprint);counts['pruned_read_nodes']+=len(pruned_reads)

    for k in ('labels_created','labels_expanded','examined_edges'):
     counts['original_'+k]+=trace[k];counts['pruned_'+k]+=pruned[k]

    native_trace,native_footprint=tracer.traced_query(row['source'],row['sink'],budget[row['connection_id']],10000);assert trace==native_trace and frozenset(footprint)==native_footprint
    cid=row['connection_id'];result=results[cid];assert trace['physical_edge_ids']==result['physical_edge_ids'] and trace['cost']==result['cost_at_search_epoch'];context=(row['net_id'],row['source'],row['sink'],budget[cid]);old=previous.get(cid);counts['queries']+=1
    if old and context[:3]==old[0][:3]:
     counts['endpoint_unchanged']+=1
     changed=result['physical_edge_ids']!=old[2]['physical_edge_ids'] or result['cost_at_search_epoch']!=old[2]['cost_at_search_epoch']
     if changed:counts['endpoint_only_false_reuse']+=1
     if context==old[0]:
      counts['endpoint_budget_unchanged']+=1
      if {n:other[n] for n in old[3] if other[n]}==old[1]:
       counts['exact_context_reusable']+=1;assert trace==old[4];assert not changed
    previous[cid]=(context,{n:other[n] for n in footprint if other[n]},result,frozenset(footprint),trace)
   if entry['accepted']:
    rows=[{**r,'physical_edge_ids':results[r['connection_id']]['physical_edge_ids']} for r in groups[net]];occ.subtract(unions[net]);unions[net]=union(rows);occ.update(unions[net]);active.update({r['connection_id']:r for r in rows})
  final=load(prior/f'step_{step}_prediction.json');assert +occ==Counter({int(n):v for n,v in final['node_occupancy'].items()});assert all(active[r['connection_id']]['physical_edge_ids']==r['physical_edge_ids'] for r in final['connections'])
  (out/f'step_{step}_cache.json').write_bytes(pruned_cache.payload())
  reports.append({'step':step,'pruned_cache_bytes':len(pruned_cache.payload()),'pruned_cache_sha256':sha(out/f'step_{step}_cache.json'),**counts});print(reports[-1],flush=True)
 assert all(sha(Path(p))==h for p,h in bindings.items());shutil.copyfile(Path(__file__),out/'source.py')
 (out/'receipt.json').write_text(json.dumps({'steps':reports,'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'scope':'Full sequential endogenous query epoch replay. Reuse certificate requires identical NET/endpoints/budget and all previously observed positive-cost read destination otherNET demands; full Python traced result equals native status/path/objective/delay/label counters, and certified subsequent result equals prior full result. Same immutable graph/electrical context/search limit. Independent exact sink-bound policy, pruned full query executed and status/path/cost/delay checked while counters intentionally differ. Pruned dependency cache checked after full oracle execution; Actual native trace queries skipped on complete dependency matches; Python/old/native-pruned full oracles still executed and never publish on cache hits. Reverse-distance preparation and oracle costs not performance measured. No native benefit, or claim that context difference necessarily changes optimum.'},indent=2)+'\n')
if __name__=='__main__':main()
