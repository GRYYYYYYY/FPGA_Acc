"""Replay actual endogenous NET epochs; test conservative exact-context reuse."""
import json,shutil
from pathlib import Path
from collections import Counter,defaultdict
from prepared_csr import read,U64
from rc_feasible_cost_region import RCFeasibleCostRegion
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments';prior=base/'adder_tree_online_rc_budget_net_sequence_v2_2026-10-06';out=base/'adder_tree_rc_feasible_region_reuse_2026-10-06';out.mkdir();bindings={}
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
   region=RCFeasibleCostRegion(manifest['nodes'],[(u,f['dest_ranks'][i],rc.increments[i],f['costs'][i]) for u in range(manifest['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0])
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
  counts=Counter({k:0 for k in ('queries','endpoint_unchanged','endpoint_budget_unchanged','endpoint_only_false_reuse','rc_region_certified')})
  for entry in journal:
   net=entry['net_id'];other=occ.copy();other.subtract(unions[net]);signature={n:v for n,v in other.items() if v and n in relevant};results={r['connection_id']:r for r in entry['connections']}
   for row in groups[net]:
    footprint=region.destinations(row['source'],row['sink'],rc.initial(row['source']),budget[row['connection_id']]);signature={n:other[n] for n in footprint if other[n]}
    cid=row['connection_id'];result=results[cid];context=(row['net_id'],row['source'],row['sink'],budget[cid]);old=previous.get(cid);counts['queries']+=1
    if old and context[:3]==old[0][:3]:
     counts['endpoint_unchanged']+=1
     changed=result['physical_edge_ids']!=old[2]['physical_edge_ids'] or result['cost_at_search_epoch']!=old[2]['cost_at_search_epoch']
     if changed:counts['endpoint_only_false_reuse']+=1
     if context==old[0]:
      counts['endpoint_budget_unchanged']+=1
      if signature==old[1]:
       counts['rc_region_certified']+=1;assert result['cost_at_search_epoch']==old[2]['cost_at_search_epoch']
       if result['physical_edge_ids']!=old[2]['physical_edge_ids']:counts['certified_equal_cost_path_difference']+=1
    previous[cid]=(context,signature,result)
   if entry['accepted']:
    rows=[{**r,'physical_edge_ids':results[r['connection_id']]['physical_edge_ids']} for r in groups[net]];occ.subtract(unions[net]);unions[net]=union(rows);occ.update(unions[net]);active.update({r['connection_id']:r for r in rows})
  final=load(prior/f'step_{step}_prediction.json');assert +occ==Counter({int(n):v for n,v in final['node_occupancy'].items()});assert all(active[r['connection_id']]['physical_edge_ids']==r['physical_edge_ids'] for r in final['connections'])
  reports.append({'step':step,**counts});print(reports[-1],flush=True)
 assert all(sha(Path(p))==h for p,h in bindings.items());shutil.copyfile(Path(__file__),out/'source.py');shutil.copyfile(root/'tools/rc_feasible_cost_region.py',out/'region_source.py')
 (out/'receipt.json').write_text(json.dumps({'steps':reports,'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'region_source_sha256':sha(out/'region_source.py'),'scope':'RC forward/reverse minimum-delay necessary region excludes impossible budget edges. Unchanged region costs preserve mathematical constrained optimum, not bounded search counters/status or canonical tie paths. Archived FOUND costs compared. Diagnostic only; lazy host distance storage and preparation not performance measured.'},indent=2)+'\n')
if __name__=='__main__':main()
