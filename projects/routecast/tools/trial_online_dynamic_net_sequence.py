"""Actual consecutive placements: lower-bound endpoint-only cache hazards."""
import json,heapq,time,os
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from affected_connections import affected
from pre_route_endpoints import sha
from cost_read_dependency_index import CostReadDependencyIndex
from dynamic_net_dijkstra import search as net_search
from streaming_prediction_audit import verify


def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments'
 sequence=base/'adder_tree_2L032_move_sequence_2026-10-06'
 audit=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 out=base/'adder_tree_online_dynamic_net_sequence_2026-10-06';out.mkdir()
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
 sp=load(sequence/'protocol.json');assert sr['protocol_sha256']==sha(sequence/'protocol.json')
 for value in sp['inputs'].values():assert sha(value['path'])==value['sha256']
 unions,occ=state(pred);active={r['connection_id']:r for r in pred['connections']};reports=[];epoch=0
 overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items())
 for step in range(4):
  start=time.monotonic()
  if step:
   detail=sr['steps'][step-1];assert all(sha(sequence/n)==h for n,h in detail['outputs_sha256'].items())
   endpoints=load(sequence/f'step_{step}_endpoints.json')
  groups=defaultdict(list)
  for row in endpoints['connections']:groups[row['net_id']].append(row)
  initial_overflow=overflow(occ);journal=[]
  for net,rows in sorted(groups.items()):
   source=rows[0]['source'];assert all(r['source']==source for r in rows)
   result,shared,examined=net_search(f,source,[r['sink'] for r in rows],unions[net],occ)
   candidates={};newunion={source};records=[]
   for row in rows:
    status,cost,path=result[row['sink']];assert status=='FOUND'
    node=source;objective=0;seen={node}
    for eid in path:
     u,i=slots[eid];assert u==node;node=f['dest_ranks'][i];assert node not in seen;seen.add(node)
     objective+=int(f['costs'][i])*(1+occ[node]-(node in unions[net]))
    assert node==row['sink'] and objective==cost
    newunion.update(seen);candidates[row['connection_id']]={**row,'physical_edge_ids':list(path),'method':'online_dynamic_net'}
    records.append({'connection_id':row['connection_id'],'cost_at_search_epoch':cost,'physical_edge_ids':path})
   staged=occ.copy();staged.subtract(unions[net]);assert all(v>=0 for v in staged.values());staged.update(newunion)
   dirty=unions[net]^newunion;old_overflow=overflow(occ)
   # Isolated serial prototype; publish a complete NET only after all witnesses.
   active.update(candidates);unions[net]=newunion;occ=staged;epoch+=1
   journal.append({'epoch':epoch,'net_id':net,'connections':records,'dirty_nodes':len(dirty),'before_overflow':old_overflow,'after_overflow':overflow(occ),'examined_edges':examined})
  prediction={'physical_graph_sha256':endpoints['graph_sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':{'online_dynamic_net':len(active)}}
  rebuilt_u,rebuilt_o=state(prediction);assert dict(rebuilt_u)==dict(unions) and +occ==rebuilt_o
  physical=verify(sp['inputs']['rr_graph']['path'],endpoints,prediction,topology=True);assert physical['all_physical_and_union_checks_passed'];assert physical['all_type_overuse_units']==overflow(occ)
  (out/f'step_{step}_prediction.json').write_text(json.dumps(prediction)+'\n');(out/f'step_{step}_journal.json').write_text(json.dumps(journal)+'\n');(out/f'step_{step}_physical.json').write_text(json.dumps(physical)+'\n')
  row={'step':step,'epoch':epoch,'connections':len(active),'nets':len(groups),'initial_overflow':initial_overflow,'final_overflow':overflow(occ),'physical_and_union_verified':True,'wall_including_offline_audit_s':time.monotonic()-start,'prediction_sha256':sha(out/f'step_{step}_prediction.json'),'journal_sha256':sha(out/f'step_{step}_journal.json'),'physical_sha256':sha(out/f'step_{step}_physical.json')};reports.append(row);print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'source.py').write_text(Path(__file__).read_text());(out/'net_search_source.py').write_text((root/'tools/dynamic_net_dijkstra.py').read_text())
 (out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'net_search_source_sha256':sha(out/'net_search_source.py'),'steps':reports,'scope':'Fixed single pass at initial+3 consecutive actual placements; complete multi-sink NET candidates update uniqueNET occupancy for subsequent NET searches and next movement, no baseline reset. No RC budget, overflow nonincrease gate, native STA/pin legal proof, atomic concurrent publication or net benefit; each query is optimal only at recorded epoch, not necessarily at end-of-pass occupancy.'},indent=2)+'\n')
if __name__=='__main__':main()
