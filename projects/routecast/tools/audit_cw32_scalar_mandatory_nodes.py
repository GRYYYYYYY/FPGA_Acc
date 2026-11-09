"""All shortest-path corridor dominators, exact node-demand lower bound."""
import json,shutil
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read,U64
from pre_route_endpoints import sha
from predict_cw32_scalar_corridor import distances

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_scalar_mandatory_nodes_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_cw32_scalar_mandatory_nodes.py','predict_cw32_scalar_corridor.py','prepared_csr.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'method':'strictly positive scalar shortest-path DAG, topological predecessor bitset intersection; mandatory nodes per connection; union per NET for demand lower bound','scope':'Exact lower bound for fixed original scalar no-regression budget, not unconstrained/native infeasibility, not RC/STA guarantee. No native route/QoR labels read.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');summary=[]
 for name in protocol['cohort']:
  prep=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;cp=json.loads((prep/'protocol.json').read_text());m,f=read(prep/'csr',cp['graph']['sha256']);base=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';br=json.loads((base/'receipt.json').read_text());assert sha(base/'prediction.json')==br['prediction_sha256'];pred=json.loads((base/'prediction.json').read_text());adj=[[] for _ in range(m['nodes'])];rev=[[] for _ in adj];cost={}
  for u in range(m['nodes']):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot];eid=f['edge_ids'][slot];c=f['costs'][slot];cost[eid]=c
    if c!=U64 and f['capacities'][u]>0 and f['capacities'][v]>0:assert c>0;adj[u].append((v,c,eid));rev[v].append((u,c,eid))
  forward={};backward={};netnodes=defaultdict(set);connections=[]
  for row in pred['connections']:
   s,t=row['source'],row['sink']
   if s not in forward:forward[s]=distances(s,adj)
   if t not in backward:backward[t]=distances(t,rev)
   ds,dt=forward[s],backward[t];budget=sum(cost[e] for e in row['physical_edge_ids']);assert ds[t]==budget;corridor={n for n,d in ds.items() if d+dt.get(n,float('inf'))==budget};dom={s:1<<s}
   for n in sorted(corridor,key=lambda n:(ds[n],n)):
    if n==s:continue
    parents=[u for u,c,eid in rev[n] if u in corridor and ds[u]+c==ds[n]];assert parents and all(ds[u]<ds[n] for u in parents);mask=dom[parents[0]]
    for u in parents[1:]:mask &= dom[u]
    dom[n]=mask|(1<<n)
   mask=dom[t];mandatory=[]
   while mask:
    bit=mask&-mask;mandatory.append(bit.bit_length()-1);mask-=bit
   assert s in mandatory and t in mandatory;netnodes[row['net_id']].update(mandatory);connections.append({'connection_id':row['connection_id'],'net_id':row['net_id'],'source':s,'sink':t,'scalar_budget':budget,'corridor_nodes':len(corridor),'mandatory_nodes':mandatory})
  demand=Counter(n for nodes in netnodes.values() for n in nodes);conflicts=[{'node':n,'type':int(f['types'][n]),'capacity':int(f['capacities'][n]),'required_unique_nets':d,'nets':sorted(net for net,nodes in netnodes.items() if n in nodes)} for n,d in sorted(demand.items()) if d>f['capacities'][n]];dest=out/name;dest.mkdir();(dest/'connections.json').write_text(json.dumps(connections)+'\n');(dest/'conflicts.json').write_text(json.dumps(conflicts,indent=2)+'\n');report={'design':name,'connections':len(connections),'mandatory_overused_nodes':len(conflicts),'mandatory_overuse_units':sum(x['required_unique_nets']-x['capacity'] for x in conflicts),'mandatory_channel_overuse_units':sum(x['required_unique_nets']-x['capacity'] for x in conflicts if x['type'] in (4,5)),'conflicts_sha256':sha(dest/'conflicts.json'),'connections_sha256':sha(dest/'connections.json'),'baseline_receipt_sha256':sha(base/'receipt.json')};summary.append(report);print(json.dumps(report),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':summary},indent=2)+'\n')
if __name__=='__main__':main()
