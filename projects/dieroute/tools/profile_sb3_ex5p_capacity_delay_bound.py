"""Exact single-connection optimistic capacity bound; never supplies a route to the router."""
import array,csv,hashlib,heapq,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_ex5p_capacity_delay_bound_20261015';B=R/'work/sb3_fixed_feedback_pair_20261015';INF=(1<<64)-1

def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(p):
  key=str(p)
  if key not in refs:refs[key]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
  return refs[key]
 protocol=json.loads((B/'protocol.json').read_text());case=next(x for x in protocol['cases'] if x['label']=='ex5p');prefix=case['input_prefix'];files=[Path(prefix+s) for s in ['.nodes','.edges','.resources','.tasks']]
 for f in files:assert sha(f)==protocol['source_sha256'][str(f)]
 nodes=list(struct.iter_unpack('<IHH',files[0].read_bytes()));edges=list(struct.iter_unpack('<IHH',files[1].read_bytes()));initial=list(struct.iter_unpack('<HHHHII',files[2].read_bytes()));task=struct.unpack_from('<IIIIHHIII',files[3].read_bytes(),895*32)
 assert task[:4]==(895,138,43804,14256);assert len(nodes)==len(initial)==336312 and all(x[0]==0 for x in initial)
 assert all(begin+count<=len(edges) for begin,count,_ in nodes) and all(v<len(nodes) for v,_,w in edges)
 source,sink=task[2:4];results=[]
 for arm in ['feedback_off','feedback_on']:
  d=B/'native_runs'/('ex5p_'+arm+'_0');proof=json.loads((d/'replay_audit.json').read_text());assert proof['cpu_legal'] and proof['final_resources_and_costs_byte_equivalent'];treefile=d/'route.route_trees.csv';resourcefile=d/'route.resources'
  for f in [treefile,resourcefile]:assert sha(f)==proof['source_sha256'][str(f)]
  members={}
  for row in csv.DictReader(treefile.open()):
   net=int(row['net_id']);members.setdefault(net,set()).update(int(row[k]) for k in ['parent','child'] if row[k]!=row['source'])
  occupancy=[0]*len(nodes)
  for ns in members.values():
   for v in ns:occupancy[v]+=1
  resources=list(struct.iter_unpack('<HHHHII',resourcefile.read_bytes()));assert len(resources)==len(nodes)
  assert all(r[0]==occupancy[v] and r[1]==initial[v][1] and r[0]<=r[1] for v,r in enumerate(resources))
  allowed=[r[0]-(v in members[138])<r[1] for v,r in enumerate(resources)];allowed[source]=True
  dist=[INF]*len(nodes);parent=[None]*len(nodes);dist[source]=0;queue=[(0,source)];popped=0
  while queue:
   cost,u=heapq.heappop(queue)
   if cost!=dist[u]:continue
   popped+=1;begin,count,_=nodes[u]
   for v,_,delay in edges[begin:begin+count]:
    if allowed[v] and cost+delay<dist[v]:dist[v]=cost+delay;parent[v]=u;heapq.heappush(queue,(cost+delay,v))
  assert dist[sink]!=INF
  # Independent optimality certificate: feasible source potential, every allowed
  # directed edge inequality, and a legal witness attaining the sink potential.
  checked=0
  assert dist[source]==0
  for u,(begin,count,_) in enumerate(nodes):
   if dist[u]==INF:continue
   assert allowed[u]
   for v,_,w in edges[begin:begin+count]:
    if allowed[v]:assert dist[v]<=dist[u]+w;checked+=1
  path=[sink]
  while path[-1]!=source:assert parent[path[-1]] is not None and len(path)<=len(nodes);path.append(parent[path[-1]])
  path.reverse();assert len(set(path))==len(path) and all(allowed[v] for v in path)
  cost=0
  for u,v in zip(path,path[1:]):
   begin,count,_=nodes[u];weights=[w for target,_,w in edges[begin:begin+count] if target==v];assert weights;cost+=min(weights)
  assert cost==dist[sink]
  last=max(d.glob('route.timing_iteration_*.input.csv'),key=lambda f:int(f.name.split('_')[-1].split('.')[0]));row=next(x for x in csv.DictReader(last.open()) if x['task_id']=='895');sha(last)
  data=array.array('Q',dist);assert data.itemsize==8
  import sys
  if sys.byteorder!='little':data.byteswap()
  artifact=P/(arm+'.distances.u64');artifact.write_bytes(data.tobytes());sha(artifact)
  results.append(dict(arm=arm,original_task_max_hops=task[5],bound_ignores_hop_limit=True,all_resource_occupancies_verified=len(nodes),other_nets_fixed=len(members)-1,reachable_nodes=popped,edge_inequalities_checked=checked,minimum_packed_delay_ps=cost,observed_final_delay_ps=int(row['delay_ps']),witness_path=path,witness_hops=len(path)-1,distance_certificate=str(artifact)))
  sha(d/'replay_audit.json')
 sha(B/'protocol.json');sha(Path(__file__).resolve())
 report=dict(status='single_connection_optimistic_capacity_delay_optima_certified',outcomes=results,source_sha256=refs,adopted=False,research_complete=False,scope='Ex5p only. Other612nets fixed; all net138 dynamic occupancy removed, SOURCE uncharged as original model. Unrestricted packed graph, no corridor, cost or hop restriction, no preservation of other five net138 connections. Witness and all reachable allowed-edge distance inequalities certify exact optimum of this relaxed problem, not a realizable full-net repair, native STA delay, globalCPD or kernel-budget improvement. Does not alter experimental routes or provide oracle input to search.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in x.items() if k!='witness_path'} for x in results]))
if __name__=='__main__':main()
