"""Enumerate every fixed original/deleted-node support combination; no routing."""
import json,pathlib,hashlib,itertools
from collections import Counter,defaultdict,deque
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_conflict_group_combinations_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);A=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';D=R/'experiments/mmc_conflict_node_detour_v1_2026-10-19';T=R/'experiments/mmc_detour_capacity_transfer_v1_2026-10-19';G=R/'experiments/mmc_conflict_group_remaining_detours_v1_2026-10-19'
 assert read(D/'independent_verification_v1.json')['status']=='ALL4_FULL_GRAPH_MINIMUM_RC_AND_SECONDARY_HOPS_CERTIFIED'
 assert read(G/'independent_verification_v1.json')['status']=='ALL6_FULL_GRAPH_MINIMUM_RC_AND_SECONDARY_HOPS_CERTIFIED'
 owner=read(T/'research_decision_v1.json')['original_support_mandatory_owners'];nets=sorted(a['net_id'] for a in owner);indices=set(read(R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/episode_01/NET_contribution_indices.json'));counts=Counter();old={};new={};penalty={};bindings={}
 for line in (A/'mandatory_contributions.jsonl').open():
  x=json.loads(line)
  if x['index'] in indices:
   nodes=set(map(int,x['mandatory_channel_sink_witness']));counts.update(nodes)
   if x['net_id'] in nets:old[x['net_id']]=nodes
 for n in nets:
  root=D if n in [1395,1400] else G
  b=read(root/f'net_{n}_original_sink_labels.json');a=read(root/f'net_{n}_blocked_sink_labels.json');assert b.keys()==a.keys()
  penalty[n]=sum(a[s][0]-b[s][0] for s in b);assert penalty[n]>0
  wp=T/f'net_{n}_mandatory_witnesses.json' if n in [1395,1400] else G/f'net_{n}_blocked_mandatory_witnesses.json';w=read(wp);new[n]=set(map(int,w));assert 646275 in old[n] and 646275 not in new[n]
  # Verify each newly mandatory channel using source-to-witness deletion BFS,
  # independently of the producer's dominator recurrence.
  if n not in [1395,1400]:
   support=read(G/f'net_{n}_blocked_support.json');children=defaultdict(list)
   for v,ps in support['choices'].items():
    for u,_ in ps:children[u].append(int(v))
   def reach(block):
    seen={support['source']};q=deque(seen)
    while q:
     for v in children[q.popleft()]:
      if v!=block and v not in seen:seen.add(v);q.append(v)
    return seen
   normal=reach(-1)
   for node in new[n]-old[n]:assert w[str(node)] in normal and w[str(node)] not in reach(node)
  for p in [wp,root/f'net_{n}_original_sink_labels.json',root/f'net_{n}_blocked_sink_labels.json']:bindings[str(p)]=sha(p)
 rows=[]
 for flags in itertools.product([False,True],repeat=5):
  c=counts.copy();detoured=[]
  for n,f in zip(nets,flags):
   if f:c.subtract(old[n]);c.update(new[n]);detoured.append(n)
  excess={v:k-1 for v,k in c.items() if k>1}
  rows.append(dict(detoured_NETs=detoured,conflict_node_mandatory_owners=c[646275],conflict_node_capacity_necessary_condition=c[646275]<=1,mandatory_overloaded_channels=len(excess),mandatory_overflow_lower_bound=sum(excess.values()),sum_sink_RC_floor_increase_units_1e18=sum(penalty[n] for n in detoured)))
 eligible=[x for x in rows if x['conflict_node_capacity_necessary_condition']];assert len(eligible)==6
 decision=dict(status='ALL32_FIXED_FIVE_NET_SUPPORT_COMBINATIONS_ENUMERATED',NETs=nets,rows=rows,node646275_capacity_necessary_combinations=6,minimum_global_mandatory_overflow_lower_bound_among_node_necessary_combinations=min(x['mandatory_overflow_lower_bound'] for x in eligible),minimum_sum_sink_RC_increase_for_any_capacity_legal_route_units_1e18=sum(penalty.values())-max(penalty.values()),per_NET_avoiding_node_sink_RC_floor_increase_units_1e18=penalty,scope='All bounds within fixed supports except aggregate RC lower bound, which uses globally certified per-sink minima in original and deleted-node full graphs. Sum of per-sink additive RC is not STA/CPD or wall time. Mandatory counts do not establish feasibility.',new_native_jobs=0)
 for p in [A/'mandatory_contributions.jsonl',D/'independent_verification_v1.json',G/'independent_verification_v1.json',T/'research_decision_v1.json',pathlib.Path(__file__).resolve()]:bindings[str(p)]=sha(p)
 decision['bindings']=bindings
 (O/'results.json').write_text(json.dumps(decision,indent=2)+'\n');print(json.dumps({k:v for k,v in decision.items() if k not in ['bindings','rows']}),flush=True)
if __name__=='__main__':main()
