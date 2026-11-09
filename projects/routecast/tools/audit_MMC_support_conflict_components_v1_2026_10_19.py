"""Input-only conflict components and disjoint capacity-clique certificates."""
import pathlib,json,hashlib
from collections import defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_support_conflict_components_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);A=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';prior=json.loads((A/'results.json').read_text());ap=M/'independent_prediction_verification_v1.json';audit=json.loads(ap.read_text());journal=A/'mandatory_contributions.jsonl';assert prior['bindings'][str(journal)]==sha(journal)
 byindex={}
 for line in journal.open():
  row=json.loads(line);byindex[row['index']]=row
 results=[];bindings={str(p):sha(p) for p in [A/'results.json',journal,ap,pathlib.Path(__file__).resolve()]}
 for case in ['episode_01','episode_02','episode_03']:
  ip=M/case/'NET_contribution_indices.json';assert audit['bindings'][str(ip)]==sha(ip);bindings[str(ip)]=sha(ip);indices=json.loads(ip.read_text());assert len(indices)==len(set(indices))==55300
  owners=defaultdict(list);netindex={}
  for i in indices:
   row=byindex[i];net=row['net_id'];assert net not in netindex;netindex[net]=i
   for node in row['mandatory_channel_sink_witness']:owners[int(node)].append(net)
  over={node:sorted(nets) for node,nets in owners.items() if len(nets)>1};adj=defaultdict(set)
  for nets in over.values():
   for net in nets:adj[net].update(set(nets)-{net})
  unseen=set(adj);components=[]
  while unseen:
   todo=[min(unseen)];seen=set(todo)
   for net in todo:
    for other in adj[net]:
     if other not in seen:seen.add(other);todo.append(other)
   unseen-=seen;components.append(sorted(seen))
  components.sort(key=lambda a:(-len(a),a))
  used=set();blocks=[]
  for node,nets in sorted(over.items(),key=lambda kv:(-len(kv[1]),kv[0])):
   selected=sorted(set(nets)-used)
   if len(selected)<2:continue
   used.update(selected);blocks.append(dict(node=node,capacity=1,members=[dict(net_id=net,contribution_index=netindex[net],dominated_sink=byindex[netindex[net]]['mandatory_channel_sink_witness'][str(node)]) for net in selected],required_support_departures=len(selected)-1))
  assert sum(len(b['members']) for b in blocks)==len(used)
  row=dict(case=case,conflicting_NETs=len(adj),conflict_edges=sum(map(len,adj.values()))//2,overloaded_channels=len(over),maximum_channel_mandatory_NETs=max(map(len,over.values())),components=components,disjoint_conflict_blocks=blocks,disjoint_block_NETs=len(used),certified_required_support_departures_lower_bound=sum(b['required_support_departures'] for b in blocks))
  (O/f'{case}.json').write_text(json.dumps(row,indent=2)+'\n');results.append({k:v for k,v in row.items() if k not in ['components','disjoint_conflict_blocks']});print(results[-1],flush=True)
 (O/'results.json').write_text(json.dumps(dict(status='ALL3_CONFLICT_COMPONENTS_AND_DISJOINT_SUPPORT_DEPARTURE_CERTIFICATES_PRODUCED',bindings=bindings,cases=results,selection='Single deterministic pass through channels ordered by descending original owner count then RRid; take remaining unused owners if at least2. No native outcomes used.',scope='Departure lower bound from original supplied shortest-parent supports only; not full-graph RC penalty or native infeasibility. Bounds need independent witness verification.'),indent=2)+'\n')
if __name__=='__main__':main()
