"""CPU sandbox: whole-net target-first exchange; no authoritative publication."""
import collections,csv,hashlib,heapq,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb3_ex5p_two_net_exchange_v2_20261015'

def main():
 assert P.exists();bindings={}
 def read(path):
  path=Path(path);data=path.read_bytes();bindings[str(path)]=hashlib.sha256(data).hexdigest();return data
 def rows(path):return list(csv.DictReader(read(path).decode().splitlines()))
 protocol=json.loads(read(R/'work/sb3_fixed_feedback_pair_20261015/protocol.json'))
 case=next(v for v in protocol['cases'] if v['label']=='ex5p')
 nodes=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.nodes')))
 edges=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.edges')))
 tasks={int(v['id']):v for v in rows(case['connections'])}
 by_net=collections.defaultdict(list)
 for task,row in tasks.items():by_net[int(row['net_id'])].append(task)
 def weight(u,v):
  start,count,_=nodes[u];values=[w for dst,_,w in edges[start:start+count] if dst==v]
  assert values,(u,v)
  return min(values)
 def path_delay(source,path):
  total=0
  for node in path:total+=weight(source,node);source=node
  return total
 frontier=json.loads(read(R/'work/sb3_ex5p_delay_frontier_20261015/independent_audit.json'))
 certificate=json.loads(read(R/'work/sb3_ex5p_delay_frontier_20261015/frontier_rebuild_audit.json'))
 for f,h in certificate['source_sha256'].items():
  read(f);assert bindings[str(Path(f))]==h,f
 outcomes=[]
 # Posterior target only: this diagnoses repair feasibility, not a general scheduler.
 target_net=138;target_task=895
 for arm in ['feedback_off','feedback_on']:
  directory=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm+'_0')
  resources=list(struct.iter_unpack('<HHHHII',read(directory/'route.resources')))
  old_paths=collections.defaultdict(list)
  for row in rows(directory/'route.paths.csv'):old_paths[int(row['task_id'])].append(int(row['resource_id']))
  old_nodes=collections.defaultdict(set);owners=collections.defaultdict(set)
  for row in rows(directory/'route.route_trees.csv'):
   net=int(row['net_id']);v=int(row['child']);old_nodes[net].add(v)
   if row['child']!=row['source']:owners[v].add(net)
  # Candidate owners come from current full-graph occupancy, not recorded release IDs.
  candidates=sorted({n for v in range(len(nodes)) if len(owners[v]-{target_net})>=resources[v][1]
                     for n in owners[v]-{target_net}})
  all_candidates=candidates
  boundary=next(v for v in frontier['outcomes'] if v['arm']==arm)
  candidates=[v['id'] for v in boundary['competing_nets']]
  assert set(candidates)<=set(all_candidates)
  old_delays={t:path_delay(int(tasks[t]['source']),old_paths[t]) for t in tasks}
  attempts=[]
  for displaced in candidates:
   group={target_net,displaced};base=[owners[v]-group for v in range(len(nodes))]
   new_paths={};new_nodes={};complete=True;expanded=0
   for net in [target_net,displaced]:
    source=int(tasks[by_net[net][0]]['source']);parent={};tree_dist={source:0};tree_depth={source:0}
    # Preserve all sinks; target connection first, remaining task IDs deterministic.
    order=sorted(by_net[net],key=lambda t:(t!=target_task,t))
    for task in order:
     sink=int(tasks[task]['sink']);max_hops=int(tasks[task]['max_hops'])
     if sink not in tree_dist:
      distances=dict(tree_dist);hops=dict(tree_depth);previous={}
      pending=[(d,tree_depth[v],v) for v,d in tree_dist.items()];heapq.heapify(pending)
      while pending:
       cost,depth,u=heapq.heappop(pending)
       if (cost,depth)!=(distances[u],hops[u]):continue
       expanded+=1
       if u==sink:break
       if depth>=max_hops:continue
       start,count,_=nodes[u]
       for v,_,w in edges[start:start+count]:
        if v in tree_dist or len(base[v])>=resources[v][1]:continue
        if (cost+w,depth+1)<(distances.get(v,1<<63),hops.get(v,1<<63)):
         distances[v]=cost+w;hops[v]=depth+1;previous[v]=u;heapq.heappush(pending,(cost+w,depth+1,v))
      if sink not in previous:complete=False;break
      branch=[];v=sink
      while v not in tree_dist:branch.append(v);v=previous[v]
      for v in reversed(branch):
       parent[v]=previous[v];tree_dist[v]=distances[v];tree_depth[v]=hops[v]
     path=[];v=sink
     while v!=source:path.append(v);v=parent[v]
     new_paths[task]=list(reversed(path))
     assert len(path)<=max_hops
    if not complete:break
    new_nodes[net]=set(parent)
    for v in parent:base[v].add(net)
   record=dict(displaced_net=displaced,complete=complete,expanded=expanded)
   if complete:
    for v in range(len(nodes)):assert len(base[v])<=resources[v][1]
    new_delays={t:path_delay(int(tasks[t]['source']),path) for t,path in new_paths.items()}
    record.update(target_delay_ps=new_delays[target_task],
     target_baseline567_reached=new_delays[target_task]<=567,
     worsened_connections=[t for t,d in new_delays.items() if d>old_delays[t]],
     old_group_wire=sum(nodes[v][2] for net in group for v in old_nodes[net]),
     new_group_wire=sum(nodes[v][2] for net in group for v in new_nodes[net]),
     paths={str(t):path for t,path in new_paths.items()})
   attempts.append(record)
   partial=dict(status='private_trials_running',current_arm=arm,current_owner=displaced,outcomes=outcomes,attempts=attempts)
   temporary=P/'partial.tmp';temporary.write_text(json.dumps(partial,indent=2)+'\n');temporary.replace(P/'partial_result.json')
   print(json.dumps(dict(arm=arm,owner=displaced,complete=complete,target_ps=record.get('target_delay_ps'))),flush=True)
  outcomes.append(dict(arm=arm,candidates=len(candidates),all_current_owner_candidates=all_candidates,certified_pruned_owners=sorted(set(all_candidates)-set(candidates)),attempts=attempts))
 read(Path(__file__).resolve())
 result=dict(status='two_net_whole_tree_sandbox_completed',outcomes=outcomes,source_sha256=bindings,
  authoritative_publication=False,adopted=False,research_complete=False,
  scope='Posterior ex5p target138/task895 feasibility diagnostic. Only independently certified necessary-frontier owners receive full-net repair; all other current owners are recorded as pruned because none can reach target<=567ps. No pruning by observed repair or native quality. Delay-only search omits negotiated costs/corridors and is not the production router. Full nets repaired privately; no native STA, full-float delay, global CPD, actual rollback/publication or general scheduling claim.')
 with (P/'result.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 for arm in outcomes:
  good=[v for v in arm['attempts'] if v['complete'] and v['target_baseline567_reached']]
  print(json.dumps(dict(arm=arm['arm'],candidates=arm['candidates'],complete=sum(v['complete'] for v in arm['attempts']),target_successes=len(good),no_delay_regression_successes=sum(not v['worsened_connections'] for v in good))))
if __name__=='__main__':main()
