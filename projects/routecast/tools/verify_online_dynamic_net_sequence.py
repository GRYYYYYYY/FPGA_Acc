"""Independent replay of per-NET cost epochs and final occupancy witnesses."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from pre_route_endpoints import sha

root=Path(__file__).resolve().parents[1]
out=root/'experiments/adder_tree_online_dynamic_net_sequence_2026-10-06'
r=json.loads((out/'receipt.json').read_text());assert sha(out/'source.py')==r['source_sha256'];assert sha(out/'net_search_source.py')==r['net_search_source_sha256'];assert all(sha(p)==h for p,h in r['inputs_sha256'].items())
p=json.loads((root/'experiments/adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json').read_text())
m,f=read(root/'experiments/adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',p['physical_graph_sha256'])
edges={f['edge_ids'][i]:(u,i) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
unions=defaultdict(set)
for row in p['connections']:
 unions[row['net_id']].add(row['source'])
 for eid in row['physical_edge_ids']:
  u,i=edges[eid];unions[row['net_id']].update((u,f['dest_ranks'][i]))
occ=Counter(n for nodes in unions.values() for n in nodes)
epoch=queries=0
overflow=lambda:sum(max(0,v-f['capacities'][n]) for n,v in occ.items())
for step in r['steps']:
 k=step['step'];predfile=out/f'step_{k}_prediction.json';journalfile=out/f'step_{k}_journal.json'
 assert sha(predfile)==step['prediction_sha256'];assert sha(journalfile)==step['journal_sha256'];assert sha(out/f'step_{k}_physical.json')==step['physical_sha256']
 final=json.loads(predfile.read_text());rows={x['connection_id']:x for x in final['connections']}
 groups=defaultdict(set)
 for x in rows.values():groups[x['net_id']].add(x['connection_id'])
 seen_nets=set()
 for item in json.loads(journalfile.read_text()):
  net=item['net_id'];assert net not in seen_nets;seen_nets.add(net);assert item['epoch']==epoch+1;assert item['before_overflow']==overflow()
  assert {x['connection_id'] for x in item['connections']}==groups[net]
  candidate=set()
  for q in item['connections']:
   row=rows[q['connection_id']];node=row['source'];seen={node};cost=0;assert q['physical_edge_ids']==row['physical_edge_ids']
   for eid in q['physical_edge_ids']:
    u,i=edges[eid];assert u==node;node=f['dest_ranks'][i];assert node not in seen;seen.add(node)
    cost+=int(f['costs'][i])*(1+occ[node]-(node in unions[net]))
   assert node==row['sink'];assert cost==q['cost_at_search_epoch'];candidate.update(seen);queries+=1
  assert len(unions[net]^candidate)==item['dirty_nodes'];occ.subtract(unions[net]);occ.update(candidate);unions[net]=candidate;epoch+=1
  assert item['after_overflow']==overflow()
 assert seen_nets==set(groups);assert +occ==Counter({int(n):v for n,v in final['node_occupancy'].items()});assert epoch==step['epoch']
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'verified_net_epochs':epoch,'verified_connection_cost_witnesses':queries,'all_complete_net_cohorts_and_final_occupancies_replayed':True,'scope':'Serial endogenous occupancy replay; no optimality at final occupancy, RC/native or concurrent atomicity proof.'},indent=2)+'\n')
print(json.dumps({'epochs':epoch,'cost_witnesses':queries,'replay_verified':True}))
