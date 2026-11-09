"""Exact delay witnesses/potentials for every frozen label-limited query."""
import json,heapq,time
from pathlib import Path
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
root=Path(__file__).resolve().parents[1];parent=root/'experiments/ex5p_bounded_history_repair_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');out=root/'experiments/ex5p_history_budget_diagnosis_2026-10-06';out.mkdir();ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';failed=[{**prior['failure']['query'],'answer':{'status':'UNREACHABLE'}}];(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'query_ids':[q['connection_id'] for q in failed],'policy':'Exact minimum additive buffered delay Dijkstra, empty demand/frozen other-NET capacities, no 1ns relaxation or native path input; diagnostic objective differs from unit-edge prediction'},indent=2)+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);records=[];start=time.monotonic();own=set();failed_net=failed[0]['net_id'];edge_dst={f['edge_ids'][slot]:f['dest_ranks'][slot] for slot in range(len(f['edge_ids']))}
for q in prior['records']:
 if q['net_id']==failed_net:own.add(q['source']);own.update(edge_dst[eid] for eid in q['answer']['physical_edge_ids'])
other={int(n):c-int(int(n) in own) for n,c in prior['ledger'].items()};other={n:c for n,c in other.items() if c};prior['budget_integer']=rc.scale//10**9
for q in failed:
 src,sink=q['source'],q['sink'];dist={src:rc.initial(src)};parents={};heap=[(dist[src],src)];expanded=0
 while heap:
  delay,u=heapq.heappop(heap)
  if delay!=dist[u]:continue
  expanded+=1
  if u==sink:break
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   dst=f['dest_ranks'][slot]
   if other.get(dst,0)>=f['capacities'][dst]:continue
   nd=delay+rc.increments[slot]
   if dst not in dist or nd<dist[dst]:dist[dst]=nd;parents[dst]=(u,f['edge_ids'][slot]);heapq.heappush(heap,(nd,dst))
 assert u==sink and f['capacities'][src]>0;path=[];node=sink
 while node!=src:node,eid=parents[node];path.append(eid)
 records.append({'query':{k:value for k,value in q.items() if k!='answer'},'delay_integer':delay,'physical_edge_ids':path[::-1],'potential_integer':[min(dist.get(n,delay),delay) for n in range(len(nodes))],'expanded':expanded,'within_original_budget':delay<=prior['budget_integer']})
result={'other_demand':other,'records':records,'scale':rc.scale,'graph_sha256':digest,'budget_integer':prior['budget_integer'],'diagnostic_seconds':time.monotonic()-start,'parent_sha256':sha(parent/'receipt.json'),'endpoint_sha256':sha(ep),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('diagnosed',len(records),'within1ns',sum(q['within_original_budget'] for q in records),'seconds',result['diagnostic_seconds'])
