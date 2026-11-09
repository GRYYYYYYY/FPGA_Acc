"""Actual consecutive placements: lower-bound endpoint-only cache hazards."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read
from affected_connections import affected
from pre_route_endpoints import sha


def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments'
 sequence=base/'adder_tree_2L032_move_sequence_2026-10-06'
 audit=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 out=base/'adder_tree_move_dynamic_cost_changes_2026-10-06';out.mkdir()
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
 reports=[]
 for step in sr['steps']:
  k=step['step'];assert all(sha(sequence/n)==h for n,h in step['outputs_sha256'].items())
  after=load(sequence/f'step_{k}_endpoints.json');new=load(audit/f'step_{k}_prediction.json');assert sha(audit/f'step_{k}_prediction.json')==ar['steps'][k-1]['prediction_sha256']
  closure=affected(endpoints,after);retained=set(closure['retained_connection_ids']);au,ao=state(pred);bu,bo=state(new)
  hazards=[];intersecting=0
  for r in pred['connections']:
   if r['connection_id'] not in retained:continue
   net=r['net_id'];delta=0;intersect=False
   for e in r['physical_edge_ids']:
    u,i=slots[e];n=f['dest_ranks'][i]
    old_other=ao[n]-(n in au[net]);new_other=bo[n]-(n in bu[net]);d=new_other-old_other
    intersect|=bool(d);delta+=int(f['costs'][i])*d
   intersecting+=intersect
   if delta:hazards.append({'connection_id':r['connection_id'],'net_id':net,'old_path_objective_delta':delta})
  (out/f'step_{k}_hazards.json').write_text(json.dumps(hazards,indent=2)+'\n')
  report={'step':k,'endpoint_closure_retained':len(retained),'retained_paths_touching_other_net_cost_change':intersecting,'retained_paths_with_changed_objective':len(hazards),'dirty_occupancy_nodes':sum(ao[n]!=bo[n] for n in set(ao)|set(bo)),'hazards_sha256':sha(out/f'step_{k}_hazards.json')};reports.append(report);print(json.dumps(report),flush=True)
  endpoints,pred=after,new
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'source.py').write_text(Path(__file__).read_text())
 (out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'steps':reports,'scope':'Actual three consecutive moves; changed scalar*(1+otherNET demand) cost on retained old paths is a necessary invalidation witness. No dynamic optimum search, RC budget, full cache parity or speedup. Endpoint-only closure remains valid for original constant-cost predictor.'},indent=2)+'\n')
if __name__=='__main__':main()
