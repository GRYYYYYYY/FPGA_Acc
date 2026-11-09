"""Fixed one-NET deletion-support replacements; capacity necessity, not routing."""
import json,pathlib,hashlib
from collections import Counter,defaultdict,deque
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_certified_v2 import prepare_csr
from NET_predecessor_mandatory_channels_v1 import mandatory
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_detour_capacity_transfer_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def reachable(p,blocked,sink):
 children=defaultdict(list)
 for v,parents in p['choices'].items():
  for u,_ in parents:children[u].append(v)
 seen={p['source']};q=deque(seen)
 while q:
  for v in children[q.popleft()]:
   if v!=blocked and v not in seen:seen.add(v);q.append(v)
 return sink in seen
 def_unused=None

def main():
 O.mkdir(exist_ok=False);A=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';D=R/'experiments/mmc_conflict_node_detour_v1_2026-10-19';proof=D/'independent_verification_v1.json';assert json.loads(proof.read_text())['status']=='ALL4_FULL_GRAPH_MINIMUM_RC_AND_SECONDARY_HOPS_CERTIFIED'
 cert=json.loads((A/'results.json').read_text())['cases'][0]['certificate'];blocked=cert['node'];graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';ip=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/episode_01/NET_contribution_indices.json';indices=set(json.loads(ip.read_text()));assert len(indices)==55300
 bindings={str(p):sha(p) for p in [A/'results.json',A/'mandatory_contributions.jsonl',proof,graph,ip,pathlib.Path(__file__).resolve()]};(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Episode01, exactly two preselected one-NET alternatives, no native labels or policy tuning; mandatory-overflow lower bounds only'),indent=2)+'\n')
 counts=Counter();old={};selected={a['net_id'] for a in cert['owners']}
 for line in (A/'mandatory_contributions.jsonl').open():
  row=json.loads(line)
  if row['index'] in indices:
   nodes={int(n) for n in row['mandatory_channel_sink_witness']};counts.update(nodes)
   if row['net_id'] in selected:old[row['net_id']]=nodes
 offsets,dest,cost,caps,kinds,_=load(graph);channels={v for v,k in enumerate(kinds) if k in ['CHANX','CHANY'] and caps[v]>0};caps[blocked]=0
 baseline={v:max(0,n-1) for v,n in counts.items() if n>1};assert len(baseline)==3796 and sum(baseline.values())==5725;rows=[]
 for owner in cert['owners']:
  net=owner['net_id'];p=prepare_csr(offsets,dest,cost,caps,kinds,owner['source'],owner['sinks'])
  labels=json.loads((D/f'net_{net}_blocked_sink_labels.json').read_text());assert all(list(p['distance'][int(s)])==label for s,label in labels.items())
  witnesses={n:s for n,s in mandatory(p).items() if n in channels};assert blocked not in witnesses
  new=set(witnesses);updated=counts.copy();updated.subtract(old[net]);updated.update(new);over={v:n-1 for v,n in updated.items() if n>1};added=sorted(v for v in over if v not in baseline);removed=sorted(v for v in baseline if v not in over)
  # Independent reachability checks for all newly forced CHANs, not dominator recomputation.
  assert all(reachable(p,-1,s) and not reachable(p,n,s) for n,s in witnesses.items() if n not in old[net])
  out=dict(net_id=net,original_mandatory_channels=len(old[net]),blocked_mandatory_channels=len(new),added_mandatory_channels=sorted(new-old[net]),removed_mandatory_channels=sorted(old[net]-new),mandatory_overloaded_channels=len(over),mandatory_overflow_lower_bound=sum(over.values()),newly_overloaded_channels=added,resolved_overloaded_channels=removed,selected_conflict_resolved=updated[blocked]<=1,new_mandatory_deletion_witnesses_verified=len(new-old[net]))
  (O/f'net_{net}_mandatory_witnesses.json').write_text(json.dumps(witnesses)+'\n');rows.append(out);print(json.dumps({k:v for k,v in out.items() if not isinstance(v,list)}),flush=True)
 (O/'results.json').write_text(json.dumps(dict(status='FIXED_ONE_NET_DETOUR_SUPPORT_CAPACITY_BOUNDS_COMPUTED',baseline_overloaded_channels=3796,baseline_overflow_lower_bound=5725,rows=rows,scope='Restricted shortest supports after forbidding one node in one NET. Counts inherit prior mandatory journal audit; new forced nodes independently deletion-checked. Neither feasibility nor native utility established.'),indent=2)+'\n')
if __name__=='__main__':main()
