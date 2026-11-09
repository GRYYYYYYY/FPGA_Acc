"""Exact minimum-delay feasibility at authenticated failed greedy state."""
import json,heapq
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_joint_integer_search_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];graph,digest,nodes,f,rc,queries,_=load(root);assert digest==prior['graph_sha256'];slots={f['edge_ids'][i]:(u,f['dest_ranks'][i],i) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);ledger=Counter();owners=defaultdict(set)
for row in prior['results'][:-1]:
 assert row['result']['status']=='FOUND';used={row['source']};node=row['source']
 for eid in row['result']['physical_edge_ids']:u,v,_=slots[eid];assert u==node;node=v;used.add(node)
 assert node==row['sink'];ledger.update(used-unions[row['net_id']]);unions[row['net_id']].update(used)
for net,used in unions.items():
 for n in used:owners[n].add(net)
failed=prior['results'][-1];assert failed['result']['status']=='UNREACHABLE';other=Counter(ledger)
for n in unions[failed['net_id']]:other[n]-=1
other=dict(+other)
def shortest(demand):
 src,sink=failed['source'],failed['sink']
 if demand.get(src,0)>=f['capacities'][src]:return {'status':'DISCONNECTED'}
 distance={src:rc.initial(src)};parents={};heap=[(distance[src],src)];expanded=0
 while heap:
  delay,u=heapq.heappop(heap)
  if delay!=distance[u]:continue
  expanded+=1
  if u==sink:
   path=[];node=u
   while node!=src:prev,eid=parents[node];path.append(eid);node=prev
   return {'status':'FOUND','delay_integer':delay,'delay_ns':float(Fraction(delay,rc.scale))*1e9,'physical_edge_ids':path[::-1],'expanded':expanded,'potential_integer':{str(n):min(distance.get(n,delay),delay) for n in range(len(nodes))}}
  for i in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][i]
   if demand.get(v,0)>=f['capacities'][v]:continue
   nd=delay+rc.increments[i]
   if v not in distance or nd<distance[v]:distance[v]=nd;parents[v]=(u,f['edge_ids'][i]);heapq.heappush(heap,(nd,v))
 return {'status':'DISCONNECTED','expanded':expanded}
native=NativeCapacityRC(rc);native.set_other(other);trials={str(ns):native.query(failed['source'],failed['sink'],(Fraction(ns,10**9)*rc.scale).__floor__(),max_labels=10000) for ns in (1,2)};minimum=shortest(other);unoccupied=shortest({});blockers=[]
for eid in unoccupied.get('physical_edge_ids',[]):
 _,v,_=slots[eid]
 if other.get(v,0)>=f['capacities'][v]:blockers.append({'node':v,'other_demand':other[v],'capacity':f['capacities'][v],'owner_nets':sorted(owners[v]-{failed['net_id']})})
out=root/'experiments/nonzero_rc_joint_failure_diagnosis_v2_2026-10-06';out.mkdir();result={'failed_query':{k:failed[k] for k in ('net_id','pin_index','source','sink')},'other_demand':other,'scale':rc.scale,'capacity_minimum_delay':minimum,'unoccupied_minimum_delay':unoccupied,'native_trials':trials,'unoccupied_shortest_path_blockers':blockers,'graph_sha256':digest,'parent_verification_sha256':sha(parent/'verification.json'),'source_sha256':sha(Path(__file__)),'context_source_sha256':sha(root/'tools/nonzero_rc_search_context.py'),'scope':'Exact nonnegative-additive minimum-delay Dijkstra on frozen other-NET capacity state; proves only current frozen-state shortest delay/disconnection, not global route infeasibility. 2ns is diagnostic relaxation, not success at1ns.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(minimum['status'],minimum.get('delay_ns'),unoccupied.get('delay_ns'),{k:v['status'] for k,v in trials.items()},blockers)
