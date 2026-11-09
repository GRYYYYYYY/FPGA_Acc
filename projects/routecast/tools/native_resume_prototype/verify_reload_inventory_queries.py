"""Independent Dijkstra, sequential owner and exact final-path replay."""
import json,sys,heapq
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[2];seq=R/'experiments/native_resume_reload_inventory_adder_2026-10-07';results=[];bindings={str(Path(__file__)):sha(Path(__file__))}
for i in (1,2,3):
 b=R/f'experiments/native_resume_reload_inventory_adder_step{i}_workflow_2026-10-07';o=b/'global_budget';r=json.loads((o/'receipt.json').read_text());p=json.loads((o/'protocol.json').read_text());assert all(sha(f)==h for f,h in p['bindings'].items());bindings.update(p['bindings']);bindings[str(o/'receipt.json')]=sha(o/'receipt.json')
 ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{i}_endpoints.json';meta=json.loads(ep.read_text());_,_,nodes,f,rc,qs=load_endpoints(ep);assert rc.scale==r['scale'];arc={f['edge_ids'][s]:(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 original=json.loads((b/'exchange/receipt.json').read_text())['records'];records={q['connection_id']:q for q in original}
 def path(q):
  ps=[(q['source'],None)];u=q['source']
  for eid in q['answer']['physical_edge_ids']:
   previous,v,sw=arc[eid];assert previous==u;ps.append((v,sw));u=v
  assert u==q['sink'];return tuple(ps)
 groups={}
 for q in original:groups.setdefault(meta['net_names'][str(q['net_id'])],[]).append(q)
 owners={name:{n for q in queries for n,sw in path(q)} for name,queries in groups.items()};occ=Counter(n for us in owners.values() for n in us);total=r['initial_wire'];count=0
 for index,row in enumerate(r['rows']):
  name=row['net'];assert sorted(owners[name])==row['old_union'];other=Counter(occ);other.subtract(owners[name]);assert {str(n):v for n,v in other.items() if v}==row['other_occupancy']
  trial=row['trial_records'];source=trial[0]['source'];pending={q['sink'] for q in trial};dist={source:rc.initial(source)};heap=[(dist[source],source)];done=set()
  while pending and heap:
   val,u=heapq.heappop(heap)
   if u in done or val!=dist[u]:continue
   done.add(u);pending.discard(u)
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if other.get(v,0)>=f['capacities'][v]:continue
    value=val+rc.increments[s]
    if value<dist.get(v,value+1):dist[v]=value;heapq.heappush(heap,(value,v))
  assert not pending;delays={x['connection_id']:x for x in row['delays']};parent={};newunion=set()
  for q in trial:
   x=delays[q['connection_id']];assert x['new_integer']==dist[q['sink']]==rc.path(source,q['sink'],q['answer']['physical_edge_ids']);assert x['old_integer']==rc.path(source,q['sink'],records[q['connection_id']]['answer']['physical_edge_ids'])
   ps=path(q);newunion.update(n for n,sw in ps)
   for (u,_),(v,sw) in zip(ps,ps[1:]):
    if v in parent:assert parent[v]==(u,sw)
    parent[v]=(u,sw)
  assert sorted(newunion)==row['new_union'] and all(other.get(n,0)+1<=f['capacities'][n] for n in newunion);assert row['previous_total_wire']==total
  decision=all(x['new_integer']<=x['old_integer'] for x in row['delays']) and any(x['new_integer']<x['old_integer'] for x in row['delays']) and row['trial_total_wire']<=r['budget'];assert decision==row['accepted']
  assert sha(o/f'net_{index}.bin')==row['payload_sha256'] and sha(o/f'net_{index}.jsonl')==row['output_sha256'];count+=len(trial)
  if decision:
   for q in trial:records[q['connection_id']]=q
   owners[name]=newunion;occ=other;occ.update(newunion);total=row['trial_total_wire']
 assert total==r['final_wire']<=r['budget'];assert records=={q['connection_id']:q for q in r['records']}
 predicted={}
 for q in records.values():predicted.setdefault(meta['net_names'][str(q['net_id'])],[]).append(path(q))
 norm=lambda p:{n:Counter(ps) for n,ps in p.items() if ps};assert norm(predicted)==norm(physical_paths(b/'exchange_canonical/design.route'))
 results.append(dict(index=i,independent_conditioned_queries=count,accepted_nets=[x['net'] for x in r['rows'] if x['accepted']],final_wire=total,exact_native_paths_match=True));print(results[-1],flush=True)
assert all(sha(f)==h for f,h in bindings.items());(seq/'query_verification.json').write_text(json.dumps(dict(rows=results,bindings=bindings,scope='Independent integer Dijkstra and sequential frozen-other owner replay; exact final native paths. Shared electrical loader. Budget CHAN span totals producer/native checked separately.'),indent=2)+'\n')
