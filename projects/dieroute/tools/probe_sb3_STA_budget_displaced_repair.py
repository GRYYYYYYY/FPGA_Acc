"""Greedy consistent whole-net repair, exact native length and incumbent delay caps."""
import collections,csv,hashlib,heapq,itertools,json,struct,xml.etree.ElementTree as ET
from pathlib import Path
from delay_bounded_wire_search import search
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_STA_budget_displaced_repair_20261015'

def main():
 refs={}
 def read(path):
  path=Path(path);data=path.read_bytes();refs[str(path)]=hashlib.sha256(data).hexdigest();return data
 def rows(path):return list(csv.DictReader(read(path).decode().splitlines()))
 protocol=json.loads(read(P/'protocol.json'))
 for path,h in protocol['source_sha256'].items():
  read(path);assert refs[str(Path(path))]==h,path
 prior_dir=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015'
 prior=json.loads(read(prior_dir/'result.json'));case=json.loads(read(prior_dir/'protocol.json'))['case']
 baseline_target_ps=int(__import__('decimal').Decimal(str(case['baseline_cpd_ns']))*1000)
 raw_nodes=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.nodes')))
 edges=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.edges')))
 tasks={int(v['id']):v for v in rows(case['connections'])};by_net=collections.defaultdict(list)
 for task,row in tasks.items():by_net[int(row['net_id'])].append(task)
 lengths=[0]*len(raw_nodes);rr=Path(case['native_case'])/'rr_graph.xml';read(rr)
 for _,element in ET.iterparse(rr,events=('end',)):
  if element.tag=='node':
   a=element.attrib;l=element.find('loc')
   if a['type'] in ['CHANX','CHANY'] and a.get('direction')!='NONE':lengths[int(a['id'])]=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
   element.clear()
  elif element.tag=='edge':element.clear()
 reverse=[[] for _ in raw_nodes]
 for u,(start,count,_) in enumerate(raw_nodes):
  for v,_,w in edges[start:start+count]:reverse[v].append((u,w))
 suffix_cache={}
 def suffix(sink):
  if sink in suffix_cache:return suffix_cache[sink]
  result=[1<<63]*len(raw_nodes);result[sink]=0;pending=[(0,sink)]
  while pending:
   value,u=heapq.heappop(pending)
   if value!=result[u]:continue
   for v,w in reverse[u]:
    if value+w<result[v]:result[v]=value+w;heapq.heappush(pending,(value+w,v))
  suffix_cache[sink]=result;return result
 def delay(source,path):
  cost=0
  for v in path:
   start,count,_=raw_nodes[source];cost+=min(w for n,_,w in edges[start:start+count] if n==v);source=v
  return cost
 outcomes=[]
 for trial in prior['outcomes']:
  displaced=trial['displaced_net'];d=prior_dir/trial['label'];owners=[set() for _ in raw_nodes];old_parent={};all_tree=rows(d/'route.route_trees.csv')
  for row in all_tree:
   net=int(row['net_id']);v=int(row['child'])
   if row['child']!=row['source']:owners[v].add(net)
   if net==displaced:old_parent[v]=int(row['parent'])
  original_arm=trial['label'].split('_owner')[0]
  original=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+original_arm+'_0')
  resources=list(struct.iter_unpack('<HHHHII',read(original/'route.resources')))
  allowed=[len(values-{displaced})<resources[v][1] for v,values in enumerate(owners)]
  # Existing exchange paths regenerate from its independently audited tree.
  source=int(tasks[by_net[displaced][0]]['source']);caps={}
  observation=rows(R/'work/sb3_native_exchange_timing_observation_20261015'/trial['label']/'observe.output.csv')
  observed={int(v['task_id']):v for v in observation}
  for task in by_net[displaced]:
   path=[];v=int(tasks[task]['sink'])
   while v!=source:path.append(v);v=old_parent[v]
   caps[task]=max(0,int(observed[task]['delay_ps'])+baseline_target_ps+int(observed[task]['slack_ps']))
  for order in itertools.permutations(sorted(by_net[displaced])):
   parent={};tree_nodes={source};steps=[];complete=True
   for task in order:
    # Keep already selected tree parents: new paths may share but not reconverge.
    filtered=[];nodes=[]
    for u,(start,count,_) in enumerate(raw_nodes):
     begin=len(filtered)
     for edge in edges[start:start+count]:
      v=edge[0]
      if v==source or (v in parent and parent[v]!=u):continue
      filtered.append(edge)
     nodes.append((begin,len(filtered)-begin,0))
    incremental=[0 if v in tree_nodes else length for v,length in enumerate(lengths)]
    result=search(nodes,filtered,allowed,incremental,source,int(tasks[task]['sink']),caps[task],maximum_labels=2097152,suffix_delay=suffix(int(tasks[task]['sink'])))
    steps.append(dict(task=task,delay_cap_ps=caps[task],**result))
    if result['status']!='optimal_path':complete=False;break
    path=result['path_nodes'];assert len(path)-1<=int(tasks[task]['max_hops'])
    for u,v in zip(path,path[1:]):
     assert v not in parent or parent[v]==u
     parent[v]=u;tree_nodes.add(v)
   record=dict(parent_trial=trial['label'],displaced_net=displaced,order=list(order),complete=complete,steps=steps)
   if complete:
    paths={}
    for task in by_net[displaced]:
     path=[];v=int(tasks[task]['sink'])
     while v!=source:path.append(v);v=parent[v]
     paths[str(task)]=list(reversed(path));assert delay(source,paths[str(task)])<=caps[task]
    record.update(old_displaced_native_wire=sum(lengths[v] for v in old_parent),new_displaced_native_wire=sum(lengths[v] for v in parent),paths=paths,parent={str(v):u for v,u in parent.items()})
   outcomes.append(record)
   temporary=P/'partial.tmp';temporary.write_text(json.dumps(dict(status='running',outcomes=outcomes),indent=2)+'\n');temporary.replace(P/'partial_result.json')
   print(json.dumps({k:record[k] for k in ['parent_trial','order','complete']}|{'old_wire':record.get('old_displaced_native_wire'),'new_wire':record.get('new_displaced_native_wire')}),flush=True)
 read(Path(__file__).resolve());read(Path(__file__).with_name('delay_bounded_wire_search.py'))
 report=dict(status='STA_budget_displaced_whole_net_repairs_complete',outcomes=outcomes,source_sha256=refs,
  adopted=False,research_complete=False,scope='All2!/3!sinkorders for each of3prior exchanges; exact native lengths, fixed othernets/targetnet, perconnection candidatecap=max(0,observednativeDelay+floor(baselineCPDps)+conservativeSinkBlockSlack);no guaranteednativeSTAacceptance,2Mlabelbudget. Greedy tree construction is not global Steiner optimum. Label exhaustion not infeasibility. No nativeSTA/globalQoR or atomic publication claim.')
 (P/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
