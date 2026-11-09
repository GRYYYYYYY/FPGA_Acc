"""Find necessary occupied frontiers for the baseline connection-delay target."""
import collections,csv,hashlib,heapq,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_ex5p_delay_frontier_20261015';B=R/'work/sb3_ex5p_capacity_delay_bound_20261015';INF=(1<<64)-1

def main():
 P.mkdir(exist_ok=False);refs={}
 def bind(f):
  key=str(f)
  if key not in refs:refs[key]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
  return refs[key]
 certificate=json.loads((B/'certificate_audit.json').read_text());bind(B/'certificate_audit.json')
 for f,h in certificate['source_sha256'].items():assert bind(f)==h,f
 protocol_path=R/'work/sb3_fixed_feedback_pair_20261015/protocol.json';protocol=json.loads(protocol_path.read_text());bind(protocol_path);case=next(v for v in protocol['cases'] if v['label']=='ex5p');prefix=case['input_prefix'];nodes=list(struct.iter_unpack('<IHH',Path(prefix+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(prefix+'.edges').read_bytes()));reverse=[[] for _ in nodes]
 for u,(begin,count,_) in enumerate(nodes):
  for v,_,w in edges[begin:begin+count]:reverse[v].append((u,w))
 sink=14256;dist=[INF]*len(nodes);dist[sink]=0;queue=[(0,sink)]
 while queue:
  cost,v=heapq.heappop(queue)
  if cost!=dist[v]:continue
  for u,w in reverse[v]:
   if cost+w<dist[u]:dist[u]=cost+w;heapq.heappush(queue,(cost+w,u))
 # Unrestricted suffix distances: source-free dual certificate plus witnesses
 # are unnecessary here: this is a lower bound checked on every original edge.
 assert dist[sink]==0
 for u,(begin,count,_) in enumerate(nodes):
  for v,_,w in edges[begin:begin+count]:
   if dist[v]!=INF:assert dist[u]<=w+dist[v]
 names={int(v['net_id']):v['net'] for v in csv.DictReader(Path(case['connections']).open())};bind(Path(case['connections']));outcomes=[]
 for arm in ['feedback_off','feedback_on']:
  d=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm+'_0');owners=collections.defaultdict(set)
  for row in csv.DictReader((d/'route.route_trees.csv').open()):
   net=int(row['net_id'])
   if net!=138:
    for k in ['parent','child']:
     if row[k]!=row['source']:owners[int(row[k])].add(net)
  resources=list(struct.iter_unpack('<HHHHII',(d/'route.resources').read_bytes()));allowed=[len(owners[v])<r[1] for v,r in enumerate(resources)];forward=[v[0] for v in struct.iter_unpack('<Q',(B/(arm+'.distances.u64')).read_bytes())];frontier={};target=567
  for u,(begin,count,_) in enumerate(nodes):
   if forward[u]==INF:continue
   assert allowed[u]
   for v,_,w in edges[begin:begin+count]:
    if not allowed[v] and dist[v]!=INF and forward[u]+w+dist[v]<=target:
     frontier.setdefault(v,[]).append(dict(source=u,edge_delay_ps=w,optimistic_total_ps=forward[u]+w+dist[v]))
  assert frontier
  records=[dict(node=v,capacity=resources[v][1],other_owners=[dict(id=n,name=names[n]) for n in sorted(owners[v])],incoming_edges=rows) for v,rows in sorted(frontier.items())]
  all_owners=sorted(set().union(*(owners[v] for v in frontier)))
  # The archived baseline is an actual <=target witness in the unrestricted
  # graph. Its first blocked node must belong to the enumerated frontier.
  baseline_file=R/'work/sb_ex5p_critical_arc_RR_binding_v5_20261015/independent_audit.json';baseline=json.loads(baseline_file.read_text());bind(baseline_file);path=next(v['path'] for v in baseline['outcomes'] if v['case']=='baseline');blocked=next(v for v in path if not allowed[v]);assert blocked in frontier
  outcomes.append(dict(arm=arm,target_packed_delay_ps=target,frontier_node_count=len(frontier),competing_net_count=len(all_owners),competing_nets=[dict(id=n,name=names[n]) for n in all_owners],baseline_first_blocked_node=blocked,frontier=records))
 bind(Path(__file__).resolve());report=dict(status='necessary_occupied_first_frontiers_for567ps_enumerated',outcomes=outcomes,source_sha256=refs,research_complete=False,adopted=False,scope='Read-only ex5p fixed-other612net relaxed graph. Every source-sink path with packed delay<=567ps must first enter an occupied node in this frontier: feasible prefix potential plus unrestricted suffix lower bound<=target. This is a necessary frontier, not minimum net cut, sufficient release set, full-net repair, scheduling policy or globalCPD result. No diagnostic path is supplied to actual router.')
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in row.items() if k!='frontier'} for row in outcomes]))
if __name__=='__main__':main()
