"""Full-RR cost-tight (no hop filtering) deletion separator for fixed budgets."""
import pathlib,json,hashlib,sys
from array import array
from collections import defaultdict,deque
from MMC_zero_node_RC_shared_CSR_v1 import load
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_frozen_budget_RC_tight_separator_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O.mkdir(exist_ok=False);A=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';B=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19';nets=[1395,1400,1404,1754,2925];ip=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/episode_01/NET_contribution_indices.json';idx=set(json.loads(ip.read_text()));trees={n:json.loads((B/f'net_{n}_original.json').read_text()) for n in nets};owners=defaultdict(list)
 for line in (A/'mandatory_contributions.jsonl').open():
  x=json.loads(line);n=x['net_id']
  if n in nets and x['index'] in idx:
   for node,sink in x['mandatory_channel_sink_witness'].items():
    if trees[n]['sink_budgets'][str(sink)]==trees[n]['sink_floors'][str(sink)]:owners[int(node)].append(dict(net_id=n,sink=sink))
 candidates=[(node,sorted(v,key=lambda x:x['net_id'])) for node,v in sorted(owners.items()) if len(v)>1];node,selected=candidates[0];selected=selected[:2];proof=B/'independent_XML_verification_v1.json';prior=json.loads(proof.read_text());assert prior['status']=='ALL10_COMPLETE_TREES_XML_RC_UNIQUE_NET_OCCUPANCY_AND_ALL32_CHOICES_PASS';graph=next(pathlib.Path(p) for p in prior['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==prior['bindings'][str(graph)];bindings={str(p):sha(p) for p in [proof,graph,ip,A/'mandatory_contributions.jsonl',pathlib.Path(__file__).resolve()]}
 for row in selected:
  n=row['net_id'];root=R/('experiments/mmc_conflict_node_detour_v1_2026-10-19' if n in [1395,1400] else 'experiments/mmc_conflict_group_remaining_detours_v1_2026-10-19');pc=root/f'net_{n}_original_potential_cost.bin';p=root/'independent_verification_v1.json';pv=json.loads(p.read_text());assert pv['bindings'][str(pc)]==sha(pc);row.update(potential_file=str(pc),source=trees[n]['source'],floor=trees[n]['sink_floors'][str(row['sink'])],budget=trees[n]['sink_budgets'][str(row['sink'])]);bindings[str(pc)]=sha(pc);bindings[str(p)]=sha(p);tp=B/f'net_{n}_original.json';assert prior['bindings'][str(tp)]==sha(tp);bindings[str(tp)]=sha(tp)
 (O/'protocol.json').write_text(json.dumps(dict(node=node,selected_NETs=selected,candidate_count=len(candidates),selection='One fixed test: minimum RRid shared mandatory channel with zero-slack stored sink witnesses, first two NET IDs. Mandatory DAG used only to nominate; final proof must cover all full-RR RC-tight edges without hop condition.',bindings=bindings,scope='Episode01 frozen diagnostic node646275-avoidance budgets, not original global RouteCast completion gate.'),indent=2)+'\n')
 offsets,dest,cost,caps,kinds,_=load(graph);assert caps[node]==1 and kinds[node] in ['CHANX','CHANY'];rows=[]
 for row in selected:
  assert sys.byteorder=='little';pc=array('Q');pc.frombytes(pathlib.Path(row['potential_file']).read_bytes());assert len(pc)==len(caps) and pc[row['source']]==0 and pc[row['sink']]==row['floor']==row['budget'];seen=bytearray(len(caps));seen[row['source']]=1;queue=deque([row['source']]);scanned=0
  while queue:
   a=queue.popleft()
   if kinds[a]=='SINK':continue
   for eid in range(offsets[a],offsets[a+1]):
    scanned+=1;b=dest[eid]
    if b!=node and caps[b]>0 and kinds[b]!='SOURCE' and not seen[b] and pc[b]==pc[a]+cost[eid]:seen[b]=1;queue.append(b)
  (O/f'net_{row["net_id"]}_cost_tight_cut.bin').write_bytes(seen);out=dict(net_id=row['net_id'],source=row['source'],sink=row['sink'],budget=row['budget'],blocked_node=node,cost_tight_reachable_vertices=sum(seen),scanned_edges=scanned,sink_unreachable_without_node=not bool(seen[row['sink']]));rows.append(out);print(out,flush=True)
 (O/'results.json').write_text(json.dumps(dict(status='FIXED_ZERO_SLACK_COST_TIGHT_CUTS_PRODUCED',rows=rows,proposed_capacity_budget_infeasibility=all(row['sink_unreachable_without_node'] for row in rows),independent_verification_pending=True),indent=2)+'\n')
if __name__=='__main__':main()
