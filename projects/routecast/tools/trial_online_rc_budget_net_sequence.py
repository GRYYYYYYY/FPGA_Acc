"""Actual consecutive placements: lower-bound endpoint-only cache hazards."""
import json,heapq,time,os
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from affected_connections import affected
from pre_route_endpoints import sha
from cost_read_dependency_index import CostReadDependencyIndex
from dynamic_net_dijkstra import search as net_search
from csr_integer_budget_search import query
from csr_exact_buffered_rc import ExactBufferedRC
from buffered_rc_context import load as load_rc
from integer_rc_context import IntegerRC
from streaming_prediction_audit import verify


def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments'
 sequence=base/'adder_tree_2L032_move_sequence_2026-10-06'
 audit=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 out=base/'adder_tree_online_rc_budget_net_sequence_2026-10-06';out.mkdir()
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
 budget_root=base/'adder_tree_online_move_rc_budgets_2026-10-06';budget_receipt=load(budget_root/'receipt.json')
 rc=IntegerRC(ExactBufferedRC(f,*load_rc(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits',endpoints['graph_sha256'])))
 assert rc.scale==budget_receipt['integer_scale']
 unions,occ=state(pred);active={r['connection_id']:r for r in pred['connections']};reports=[];epoch=0
 overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items())
 for step in range(4):
  start=time.monotonic()
  if step:
   detail=sr['steps'][step-1];assert all(sha(sequence/n)==h for n,h in detail['outputs_sha256'].items())
   endpoints=load(sequence/f'step_{step}_endpoints.json')
  groups=defaultdict(list)
  for row in endpoints['connections']:groups[row['net_id']].append(row)
  budgetfile=budget_root/f'step_{step}_budgets.json';assert sha(budgetfile)==budget_receipt['steps'][step]['budget_sha256'];budgets={r['connection_id']:r['scaled_integer_budget'] for r in load(budgetfile)}
  reference_file=base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if step==0 else audit/f'step_{step}_prediction.json'
  assert sha(reference_file)==budget_receipt['steps'][step]['reference_prediction_sha256'];reference={r['connection_id']:r for r in load(reference_file)['connections']};restored=[]
  # Restore complete NETs only when new endpoints/budgets invalidate old witnesses.
  for net,rows in sorted(groups.items()):
   if any(any(active[r['connection_id']][key]!=r[key] for key in ('net_id','source','sink')) or rc.path(r['source'],r['sink'],active[r['connection_id']]['physical_edge_ids'])>budgets[r['connection_id']] for r in rows):
    restored.append(net)
    for r in rows:active[r['connection_id']]=reference[r['connection_id']]
  unions=defaultdict(set)
  for r in active.values():
   unions[r['net_id']].add(r['source'])
   for eid in r['physical_edge_ids']:
    u,i=slots[eid];unions[r['net_id']].update((u,f['dest_ranks'][i]))
  occ=Counter(n for nodes in unions.values() for n in nodes)
  initial_overflow=overflow(occ);journal=[]
  for net,rows in sorted(groups.items()):
   source=rows[0]['source'];assert all(r['source']==source for r in rows)
   result={};examined=0;statuses={}
   for r in rows:
    found=query(rc,source,r['sink'],budgets[r['connection_id']],lambda u,i:f['costs'][i]!=(1<<64)-1 and f['capacities'][f['dest_ranks'][i]]>0,lambda u,i:int(f['costs'][i])*(1+occ[f['dest_ranks'][i]]-(f['dest_ranks'][i] in unions[net])),10000)
    result[r['connection_id']]=(found['status'],found['cost'],found['physical_edge_ids']);examined+=found['examined_edges'];statuses[r['connection_id']]=found['status']
   candidates={};newunion={source};records=[];allfound=True
   for row in rows:
    status,cost,path=result[row['connection_id']]
    if status!='FOUND':allfound=False;continue
    assert rc.path(source,row['sink'],path)<=budgets[row['connection_id']]
    node=source;objective=0;seen={node}
    for eid in path:
     u,i=slots[eid];assert u==node;node=f['dest_ranks'][i];assert node not in seen;seen.add(node)
     objective+=int(f['costs'][i])*(1+occ[node]-(node in unions[net]))
    assert node==row['sink'] and objective==cost
    newunion.update(seen);candidates[row['connection_id']]={**row,'physical_edge_ids':list(path),'method':'online_dynamic_net'}
    records.append({'connection_id':row['connection_id'],'cost_at_search_epoch':cost,'physical_edge_ids':path})
   before=overflow(occ);accepted=False;candidate_overflow=None;tree_ok=True
   if allfound:
    unique={eid for r in candidates.values() for eid in r['physical_edge_ids']};incoming=Counter();outgoing=defaultdict(list)
    for eid in unique:
     u,i=slots[eid];v=f['dest_ranks'][i];incoming[v]+=1;outgoing[u].append(v)
    tree_ok=not incoming[source] and all(v<=1 or f['types'][n]==3 for n,v in incoming.items())
    degree={n:incoming[n] for n in newunion};queue=[n for n in newunion if degree[n]==0];visited=0
    while queue:
     n=queue.pop();visited+=1
     for v in outgoing[n]:
      degree[v]-=1
      if degree[v]==0:queue.append(v)
    tree_ok=tree_ok and visited==len(newunion)
    staged=occ.copy();staged.subtract(unions[net]);assert all(v>=0 for v in staged.values());staged.update(newunion);candidate_overflow=overflow(staged)
    if tree_ok and candidate_overflow<=before:
     active.update(candidates);unions[net]=newunion;occ=staged;accepted=True
   epoch+=1
   journal.append({'epoch':epoch,'net_id':net,'statuses':statuses,'accepted':accepted,'tree_ok':tree_ok,'connections':records,'before_overflow':before,'candidate_overflow':candidate_overflow,'after_overflow':overflow(occ),'examined_edges':examined})
  prediction={'physical_graph_sha256':endpoints['graph_sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':{'online_dynamic_net':len(active)}}
  for r in prediction['connections']:assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])<=budgets[r['connection_id']]
  rebuilt_u,rebuilt_o=state(prediction);assert dict(rebuilt_u)==dict(unions) and +occ==rebuilt_o
  physical=verify(sp['inputs']['rr_graph']['path'],endpoints,prediction,topology=True);assert physical['all_physical_and_union_checks_passed'];assert physical['all_type_overuse_units']==overflow(occ)
  (out/f'step_{step}_prediction.json').write_text(json.dumps(prediction)+'\n');(out/f'step_{step}_journal.json').write_text(json.dumps(journal)+'\n');(out/f'step_{step}_physical.json').write_text(json.dumps(physical)+'\n')
  row={'step':step,'epoch':epoch,'connections':len(active),'nets':len(groups),'initial_overflow':initial_overflow,'final_overflow':overflow(occ),'physical_and_union_verified':True,'restored_same_layout_baseline_nets':len(restored),'accepted_nets':sum(x['accepted'] for x in journal),'all_final_rc_budgets_met':True,'wall_including_offline_audit_s':time.monotonic()-start,'prediction_sha256':sha(out/f'step_{step}_prediction.json'),'journal_sha256':sha(out/f'step_{step}_journal.json'),'physical_sha256':sha(out/f'step_{step}_physical.json')};reports.append(row);print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'source.py').write_text(Path(__file__).read_text());(out/'net_search_source.py').write_text((root/'tools/dynamic_net_dijkstra.py').read_text())
 (out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'net_search_source_sha256':sha(out/'net_search_source.py'),'steps':reports,'scope':'One fixed RC-budget integer Pareto pass at initial+3 actual moves, 10000 labels; repair only NETs invalid under new endpoints or budgets using same-placement baseline, preserve other prior paths. Complete candidate accepted only all FOUND, acyclic no internal reconvergence, global overflow nonincrease; rejected NET stays unchanged. Serial isolated staging; final endpoint/XML/occupancy/RC audit before artifact publication. No native STA/pin legality/concurrent atomicity/net benefit proof; repair can change cross-layout overflow.'},indent=2)+'\n')
if __name__=='__main__':main()
