"""Independent node-deletion shortest-path certificates for lower-bound conflicts."""
import heapq,json
from pathlib import Path
from prepared_csr import read,U64
from pre_route_endpoints import sha

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_scalar_mandatory_nodes_2026-10-06';rec=json.loads((out/'receipt.json').read_text());reports=[]
 for r in rec['results']:
  d=out/r['design'];assert sha(d/'conflicts.json')==r['conflicts_sha256'] and sha(d/'connections.json')==r['connections_sha256'];conflicts=json.loads((d/'conflicts.json').read_text());connections=json.loads((d/'connections.json').read_text());prep=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/r['design'];p=json.loads((prep/'protocol.json').read_text());m,f=read(prep/'csr',p['graph']['sha256']);checked=0
  for conflict in conflicts:
   removed=conflict['node'];assert len(conflict['nets'])==conflict['required_unique_nets']>f['capacities'][removed]
   for net in conflict['nets']:
    c=next(c for c in connections if c['net_id']==net and removed in c['mandatory_nodes']);s,t=c['source'],c['sink'];budget=c['scalar_budget'];dist={};q=[]
    if s!=removed:dist[s]=0;q=[(0,s)]
    found=False
    while q:
     value,u=heapq.heappop(q)
     if value!=dist[u]:continue
     if u==t:found=True;break
     for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
      v=f['dest_ranks'][slot];base=f['costs'][slot]
      if v==removed or base==U64 or f['capacities'][v]==0:continue
      nd=value+base
      if nd<=budget and nd<dist.get(v,float('inf')):dist[v]=nd;heapq.heappush(q,(nd,v))
    assert not found;checked+=1
  reports.append({'design':r['design'],'node_net_deletion_certificates':checked,'all_conflicts_confirmed':True});print(json.dumps(reports[-1]),flush=True)
 (out/'deletion_verification.json').write_text(json.dumps({'parent_receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(__file__),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
