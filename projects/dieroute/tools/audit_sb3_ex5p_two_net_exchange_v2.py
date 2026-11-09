"""Verify every completed private exchange from paths and original authority."""
import collections,csv,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb3_ex5p_two_net_exchange_v2_20261015'

def main():
 bindings={}
 def load(path):
  path=Path(path);data=path.read_bytes();bindings[str(path)]=hashlib.sha256(data).hexdigest();return data
 def rows(path):return list(csv.DictReader(load(path).decode().splitlines()))
 result=json.loads(load(P/'result.json'))
 for path,expected in result['source_sha256'].items():
  load(path);assert bindings[str(Path(path))]==expected,path
 protocol=json.loads(load(R/'work/sb3_fixed_feedback_pair_20261015/protocol.json'))
 case=next(v for v in protocol['cases'] if v['label']=='ex5p')
 nodes=list(struct.iter_unpack('<IHH',load(case['input_prefix']+'.nodes')))
 edges=list(struct.iter_unpack('<IHH',load(case['input_prefix']+'.edges')))
 tasks={int(v['id']):v for v in rows(case['connections'])};by_net=collections.defaultdict(set)
 for task,row in tasks.items():by_net[int(row['net_id'])].add(task)
 def delay(source,path):
  value=0
  for v in path:
   start,count,_=nodes[source];weights=[w for dst,_,w in edges[start:start+count] if dst==v]
   assert weights,(source,v)
   value+=min(weights);source=v
  return value
 outcomes=[]
 for arm in result['outcomes']:
  directory=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm['arm']+'_0')
  resources=list(struct.iter_unpack('<HHHHII',load(directory/'route.resources')))
  owners=collections.defaultdict(set);old_members=collections.defaultdict(set)
  for row in rows(directory/'route.route_trees.csv'):
   net=int(row['net_id']);v=int(row['child']);old_members[net].add(v)
   if row['child']!=row['source']:owners[v].add(net)
  old_paths=collections.defaultdict(list)
  for row in rows(directory/'route.paths.csv'):old_paths[int(row['task_id'])].append(int(row['resource_id']))
  seen=set();completed=0;target_success=0;guarded_success=[]
  for attempt in arm['attempts']:
   other=attempt['displaced_net'];assert other!=138 and other not in seen;seen.add(other)
   if not attempt['complete']:
    assert 'paths' not in attempt
    continue
   completed+=1;group={138,other};paths={int(k):v for k,v in attempt['paths'].items()}
   assert set(paths)==by_net[138]|by_net[other]
   parents={net:{} for net in group};members={net:set() for net in group};worsened=[]
   for task,path in paths.items():
    row=tasks[task];source=int(row['source']);net=int(row['net_id'])
    assert path and path[-1]==int(row['sink'])
    assert len(path)<=int(row['max_hops']) and len(set([source]+path))==len(path)+1
    previous=source
    for node in path:
     assert node!=source
     assert parents[net].get(node,previous)==previous,'non-tree reconvergence'
     parents[net][node]=previous;members[net].add(node);previous=node
    value=delay(source,path)
    if value>delay(source,old_paths[task]):worsened.append(task)
    if task==895:assert value==attempt['target_delay_ps']
   assert sorted(worsened)==sorted(attempt['worsened_connections'])
   for v,resource in enumerate(resources):
    occupancy=len(owners[v]-group)+sum(v in members[net] for net in group)
    assert occupancy<=resource[1],(arm['arm'],other,v,occupancy)
   old_wire=sum(nodes[v][2] for net in group for v in old_members[net])
   new_wire=sum(nodes[v][2] for net in group for v in members[net])
   assert (old_wire,new_wire)==(attempt['old_group_wire'],attempt['new_group_wire'])
   assert attempt['target_baseline567_reached']==(attempt['target_delay_ps']<=567)
   if attempt['target_baseline567_reached']:
    target_success+=1
    if not worsened and new_wire<=old_wire:guarded_success.append(other)
  expected={net for v in range(len(nodes)) if len(owners[v]-{138})>=resources[v][1] for net in owners[v]-{138}}
  frontier=json.loads(load(R/'work/sb3_ex5p_delay_frontier_20261015/independent_audit.json'))
  certified=json.loads(load(R/'work/sb3_ex5p_delay_frontier_20261015/frontier_rebuild_audit.json'))
  for name,h in certified['source_sha256'].items():
   load(name);assert bindings[str(Path(name))]==h,name
  necessary={v['id'] for v in next(v for v in frontier['outcomes'] if v['arm']==arm['arm'])['competing_nets']}
  assert set(arm['all_current_owner_candidates'])==expected
  assert set(arm['certified_pruned_owners'])==expected-necessary
  assert seen==necessary and len(seen)==arm['candidates']
  outcomes.append(dict(arm=arm['arm'],candidates=len(seen),complete=completed,target_successes=target_success,
                       packed_delay_and_wire_guard_success_nets=guarded_success))
 load(Path(__file__).resolve())
 audit=dict(status='private_two_net_paths_connectivity_tree_capacity_delay_and_wire_independently_verified',outcomes=outcomes,
  source_sha256=bindings,adopted=False,research_complete=False,
  scope='Complete trials checked from paths; failed searches do not prove infeasibility. Packed-delay and node-delay_class wire proxy only; native QoR, general policy, authority versions and actual atomic publication remain unverified.')
 with (P/'independent_audit.json').open('x') as stream:json.dump(audit,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=audit['status'],outcomes=outcomes)))
if __name__=='__main__':main()
