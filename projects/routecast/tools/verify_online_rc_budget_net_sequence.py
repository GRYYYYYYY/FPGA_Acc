"""Replay repairs, complete NET decisions, search epoch costs and RC budgets."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from pre_route_endpoints import sha
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'adder_tree_online_rc_budget_net_sequence_v2_2026-10-06'
r=json.loads((out/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['inputs_sha256'].items());assert all(sha(out/'sources'/n)==h for n,h in r['sources_sha256'].items());assert sha(out/'source.py')==r['source_sha256']
p=json.loads((base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json').read_text());active={x['connection_id']:x for x in p['connections']}
m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',p['physical_graph_sha256']);rc=IntegerRC(ExactBufferedRC(f,*load(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits',p['physical_graph_sha256'])))
edges={f['edge_ids'][i]:(u,i) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
def union(rows):
 result=set()
 for row in rows:
  result.add(row['source'])
  for e in row['physical_edge_ids']:
   u,i=edges[e];result.update((u,f['dest_ranks'][i]))
 return result
budgetroot=base/'adder_tree_online_move_rc_budgets_2026-10-06';br=json.loads((budgetroot/'receipt.json').read_text());epoch=queries=rejects=0
for step in r['steps']:
 k=step['step'];pf=out/f'step_{k}_prediction.json';jf=out/f'step_{k}_journal.json';assert sha(pf)==step['prediction_sha256'] and sha(jf)==step['journal_sha256'];assert sha(out/f'step_{k}_physical.json')==step['physical_sha256'];final=json.loads(pf.read_text())
 bf=budgetroot/f'step_{k}_budgets.json';assert sha(bf)==br['steps'][k]['budget_sha256'];budgets={x['connection_id']:x for x in json.loads(bf.read_text())};groups=defaultdict(list)
 for row in budgets.values():groups[row['net_id']].append(row)
 referencefile=base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if k==0 else base/'adder_tree_2L032_move_sequence_audit_2026-10-06'/f'step_{k}_prediction.json';assert sha(referencefile)==br['steps'][k]['reference_prediction_sha256'];ref={x['connection_id']:x for x in json.loads(referencefile.read_text())['connections']};restored=0
 for net,rows in groups.items():
  if any(any(active[x['connection_id']][key]!=x[key] for key in ('net_id','source','sink')) or rc.path(x['source'],x['sink'],active[x['connection_id']]['physical_edge_ids'])>x['scaled_integer_budget'] for x in rows):
   restored+=1
   for x in rows:active[x['connection_id']]=ref[x['connection_id']]
 assert restored==step['restored_same_layout_baseline_nets']
 unions={net:union([active[x['connection_id']] for x in rows]) for net,rows in groups.items()};occ=Counter(n for nodes in unions.values() for n in nodes);overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items())
 for item in json.loads(jf.read_text()):
  epoch+=1;assert item['epoch']==epoch;net=item['net_id'];assert set(map(int,item['statuses']))=={x['connection_id'] for x in groups[net]};assert item['before_overflow']==overflow(occ);candidate={}
  for q in item['connections']:
   x=budgets[q['connection_id']];path=q['physical_edge_ids'];assert rc.path(x['source'],x['sink'],path)<=x['scaled_integer_budget'];cost=sum(int(f['costs'][edges[e][1]])*(1+occ[f['dest_ranks'][edges[e][1]]]-(f['dest_ranks'][edges[e][1]] in unions[net])) for e in path);assert cost==q['cost_at_search_epoch'];candidate[x['connection_id']]={key:x[key] for key in ('connection_id','net_id','source','sink')}|{'physical_edge_ids':path,'method':'online_dynamic_net'};queries+=1
  if item['accepted']:
   assert set(candidate)=={x['connection_id'] for x in groups[net]};assert all(status=='FOUND' for status in item['statuses'].values()) and item['tree_ok'];newunion=union(candidate.values());staged=occ.copy();staged.subtract(unions[net]);staged.update(newunion);assert overflow(staged)==item['candidate_overflow']<=overflow(occ);active.update(candidate);unions[net]=newunion;occ=staged
  else:rejects+=1
  assert overflow(occ)==item['after_overflow']
 assert sorted(active.values(),key=lambda x:x['connection_id'])==final['connections'];assert +occ==Counter({int(n):v for n,v in final['node_occupancy'].items()});assert overflow(occ)==step['final_overflow']
 for x in active.values():assert rc.path(x['source'],x['sink'],x['physical_edge_ids'])<=budgets[x['connection_id']]['scaled_integer_budget']
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'epochs':epoch,'candidate_cost_rc_witnesses':queries,'rejected_net_epochs':rejects,'all_repairs_decisions_final_paths_and_occupancies_replayed':True,'scope':'Serial RC search/budget replay plus archived XML physical audits; not independent STA or whole-move failure injection.'},indent=2)+'\n');print(epoch,queries,rejects)
