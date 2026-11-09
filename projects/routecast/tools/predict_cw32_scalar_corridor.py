"""Shortest scalar corridor search with congestion tie selection, fixed cohort."""
import heapq,json,time,shutil
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read,U64
from pre_route_endpoints import sha
from streaming_prediction_audit import verify


def distances(start,adj):
 d={start:0};q=[(0,start)]
 while q:
  value,u=heapq.heappop(q)
  if value!=d[u]:continue
  for v,base,eid in adj[u]:
   candidate=value+base
   if candidate<d.get(v,float('inf')):d[v]=candidate;heapq.heappush(q,(candidate,v))
 return d

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_scalar_corridor_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('predict_cw32_scalar_corridor.py','prepared_csr.py','pre_route_endpoints.py','streaming_prediction_audit.py','physical_prediction_audit.py','net_union_topology.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'iterations':3,'order':'ascending NET/CID; wholeNET rip-up; each sink separate corridor search, full NET union demand','budget':'fixed baseline scalar; assert baseline equals unconstrained shortest scalar; edge allowed iff dist_SOURCE[u]+base_edge+dist_to_SINK[v]==budget','tie_cost':'base_edge*(1+other_net_demand/capacity+historical_overuse/capacity), ceiling integer','sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Scalar budget enforced during search; RC not constrained here. Independent per-sink corridors may reconverge; no native route-tree or pin legality claim. Fixed three iterations, no best-iteration selection.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 for name in protocol['cohort']:
  start=time.monotonic();dest=out/name;dest.mkdir();front=root/'experiments/multiplier_family_endpoints_cw32_2026-10-06'/name;fp=json.loads((front/'protocol.json').read_text());graph=fp['inputs']['rr_graph'];ep=json.loads((front/'endpoints.json').read_text());baseline=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';br=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'prediction.json')==br['prediction_sha256'];old=json.loads((baseline/'prediction.json').read_text());oldrows={r['connection_id']:r for r in old['connections']};m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',graph['sha256']);adj=[[] for _ in range(m['nodes'])];reverse=[[] for _ in adj];edge={};cost={}
  for u in range(m['nodes']):
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot];eid=f['edge_ids'][slot];base=f['costs'][slot];edge[eid]=(u,v);cost[eid]=base
    if base!=U64 and f['capacities'][u]>0 and f['capacities'][v]>0:adj[u].append((v,base,eid));reverse[v].append((u,base,eid))
  groups=defaultdict(list)
  for r in old['connections']:groups[r['net_id']].append(r)
  def union(rows):
   used=set()
   for r in rows:
    used.add(r['source'])
    for eid in r['physical_edge_ids']:used.update(edge[eid])
   return used
  source_dist={};sink_dist={};corridors={};budgets={}
  for r in old['connections']:
   s,t=r['source'],r['sink'];source_dist.setdefault(s,None);sink_dist.setdefault(t,None)
  for s in source_dist:source_dist[s]=distances(s,adj)
  for t in sink_dist:sink_dist[t]=distances(t,reverse)
  for r in old['connections']:
   cid=r['connection_id'];s,t=r['source'],r['sink'];budget=sum(cost[eid] for eid in r['physical_edge_ids']);assert budget==source_dist[s][t];budgets[cid]=budget;corridor=defaultdict(list)
   for u,arcs in enumerate(adj):
    for v,base,eid in arcs:
     if source_dist[s].get(u,float('inf'))+base+sink_dist[t].get(v,float('inf'))==budget:corridor[u].append((v,base,eid))
   corridors[cid]=corridor
  active=dict(oldrows);unions={net:union(rows) for net,rows in groups.items()};occ=Counter(n for used in unions.values() for n in used);history=Counter();trace=[]
  for iteration in range(1,4):
   for net,rows in sorted(groups.items()):
    occ.subtract(unions[net]);assert all(v>=0 for v in occ.values());newrows=[]
    for r in rows:
     cid=r['connection_id'];s,t=r['source'],r['sink'];d={s:0};q=[(0,s)];parent={}
     while q:
      value,u=heapq.heappop(q)
      if value!=d[u]:continue
      if u==t:break
      for v,base,eid in corridors[cid].get(u,()):
       cap=f['capacities'][v];weighted=(base*(cap+occ[v]+history[v])+cap-1)//cap;candidate=value+weighted
       if candidate<d.get(v,float('inf')):d[v]=candidate;parent[v]=(u,eid);heapq.heappush(q,(candidate,v))
     assert t in d;node=t;path=[]
     while node!=s:node,eid=parent[node];path.append(eid)
     path.reverse();assert sum(cost[eid] for eid in path)==budgets[cid];newrows.append({**r,'physical_edge_ids':path,'method':'scalar_corridor'})
    active.update({r['connection_id']:r for r in newrows});unions[net]=union(newrows);occ.update(unions[net])
   excess={n:max(0,v-f['capacities'][n]) for n,v in occ.items()};history.update({n:v for n,v in excess.items() if v});trace.append({'iteration':iteration,'overuse':sum(excess.values())})
  prediction={'physical_graph_sha256':graph['sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':{'scalar_corridor':len(active)}};audit=verify(graph['path'],ep,prediction,topology=True);assert audit['all_physical_and_union_checks_passed'];(dest/'prediction.json').write_text(json.dumps(prediction)+'\n');(dest/'audit.json').write_text(json.dumps(audit)+'\n');(dest/'trace.json').write_text(json.dumps(trace,indent=2)+'\n');report={'design':name,'connections':len(active),'all_original_scalar_budgets_met':True,'overuse':audit['all_type_overuse_units'],'changed_connections':sum(active[c]['physical_edge_ids']!=oldrows[c]['physical_edge_ids'] for c in active),'wall_s':time.monotonic()-start,'prediction_sha256':sha(dest/'prediction.json'),'audit_sha256':sha(dest/'audit.json'),'baseline_receipt_sha256':sha(baseline/'receipt.json')};reports.append(report);print(json.dumps(report),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
