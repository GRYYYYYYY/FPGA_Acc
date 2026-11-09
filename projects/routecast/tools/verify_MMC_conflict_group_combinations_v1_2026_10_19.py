"""Independent per-resource reconstruction of every fixed group mask."""
import json,pathlib,hashlib
from collections import defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_conflict_group_combinations_v1_2026-10-19'
def main():
 rp=O/'results.json';x=json.loads(rp.read_text())
 for path,h in x['bindings'].items():assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()==h
 nets=x['NETs'];indices=set(json.loads((R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/episode_01/NET_contribution_indices.json').read_text()));fixed=defaultdict(set);original={};blocked={};penalty={}
 for line in (R/'experiments/mmc_NET_support_capacity_v1_2026-10-19/mandatory_contributions.jsonl').open():
  row=json.loads(line)
  if row['index'] not in indices:continue
  nodes=set(map(int,row['mandatory_channel_sink_witness']))
  if row['net_id'] in nets:original[row['net_id']]=nodes
  else:
   for node in nodes:fixed[node].add(row['net_id'])
 for net in nets:
  old=net in [1395,1400];d=R/('experiments/mmc_conflict_node_detour_v1_2026-10-19' if old else 'experiments/mmc_conflict_group_remaining_detours_v1_2026-10-19');wp=(R/f'experiments/mmc_detour_capacity_transfer_v1_2026-10-19/net_{net}_mandatory_witnesses.json') if old else d/f'net_{net}_blocked_mandatory_witnesses.json';blocked[net]=set(map(int,json.loads(wp.read_text())))
  before=json.loads((d/f'net_{net}_original_sink_labels.json').read_text());after=json.loads((d/f'net_{net}_blocked_sink_labels.json').read_text());assert before.keys()==after.keys();penalty[net]=sum(after[s][0] for s in after)-sum(before[s][0] for s in before)
 domain=set(fixed)
 for groups in [original,blocked]:
  for nodes in groups.values():domain.update(nodes)
 checked=set()
 for row in x['rows']:
  chosen=frozenset(row['detoured_NETs']);assert chosen not in checked and chosen<=set(nets);checked.add(chosen);over=0;units=0;selected_count=0
  for node in domain:
   count=len(fixed.get(node,()))+sum(node in (blocked[net] if net in chosen else original[net]) for net in nets)
   if count>1:over+=1;units+=count-1
   if node==646275:selected_count=count
  assert [over,units,selected_count]==[row['mandatory_overloaded_channels'],row['mandatory_overflow_lower_bound'],row['conflict_node_mandatory_owners']]
  assert row['sum_sink_RC_floor_increase_units_1e18']==sum(penalty[net] for net in chosen)
 assert len(checked)==32
 eligible=[r for r in x['rows'] if r['conflict_node_mandatory_owners']<=1];assert len(eligible)==6
 assert min(r['sum_sink_RC_floor_increase_units_1e18'] for r in eligible)==x['minimum_sum_sink_RC_increase_for_any_capacity_legal_route_units_1e18']
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL32_GROUP_RESOURCE_BOUNDS_AND_RC_AGGREGATES_RECONSTRUCTED',cases=32,resources_per_case=len(domain),results_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),verifier_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),scope='Reconstruction from bound mandatory sets and globally certified sink minima; not independent full dominator recomputation or feasible route proof.'),f,indent=2)
 print('ALL32_GROUP_RESOURCE_BOUNDS_AND_RC_AGGREGATES_RECONSTRUCTED',flush=True)
if __name__=='__main__':main()
