"""Private leaf-tail rerouting with complete original trees retained on rejection."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,os,struct,time
from occupied_tree_delay_search import search
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_shared_chain_probe_20261020'
def rows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((D/'protocol.json').read_text())
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 assert not (D/'manifest.json').exists();state={'status':'tail_probes_running','pid':os.getpid(),'probes':[],'adopted':False,'research_complete':False}
 def save():
  t=D/'manifest.tmp';t.write_text(json.dumps(state,indent=2)+'\n');t.replace(D/'manifest.json')
 save();allrows=rows(p['candidate_tree']);by_net=collections.defaultdict(list)
 for row in allrows:by_net[int(row['net_id'])].append(row)
 tasks=rows(p['connections']);timing={int(v['task_id']):int(v['criticality_q']) for v in rows(p['timing'])}
 handles=[open(p[k],'rb') for k in ['nodes','edges','resources','boxes']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nodes,edges,resources,boxes=maps
 def adjacency(u):
  start,count,_=struct.unpack_from('<IHH',nodes,8*u)
  for e in range(start,start+count):
   v,_,delay=struct.unpack_from('<IHH',edges,8*e);yield v,delay
 def delay(u,v):return min(w for dest,w in adjacency(u) if dest==v)
 for net in p['nets']:
  start=time.monotonic_ns();folder=D/('net_'+str(net));folder.mkdir();parent={int(v['child']):int(v['parent']) for v in by_net[net]};record={'net':net,'steps':[],'accepted_private_branches':0};state['probes'].append(record);save()
  owners=collections.Counter()
  for other,values in by_net.items():
   if other!=net:owners.update({int(v[k]) for v in values for k in ['source','parent','child']})
  actual_tasks=[v for v in tasks if int(v['net_id'])==net];source=int(actual_tasks[0]['source']);sinks={int(v['sink']) for v in actual_tasks};degree=collections.Counter(parent.values());anchors=sinks|{v for v,count in degree.items() if count>1}|{source}
  downstream=collections.Counter()
  for target in sinks:
   v=target
   while v!=source:downstream[v]+=1;v=parent[v]
  selected=[{'id':v,'sink':v} for v in sorted(anchors-{source},key=lambda v:(-downstream[v],v))]
  for task in selected:
   sink=int(task['sink']);degree=collections.Counter(parent.values());tail=[];v=sink
   while v!=source:
    tail.append(v);u=parent[v]
    if u==source or degree[u]>1 or u in sinks:attachment=u;break
    v=u
   else:raise AssertionError('Empty tail')
   remaining={v:u for v,u in parent.items() if v not in set(tail)};old_delay=sum(delay(parent[v],v) for v in tail)
   a=struct.unpack_from('<4H',boxes,8*attachment);b=struct.unpack_from('<4H',boxes,8*sink);margin=p['box_margin'];window=(max(0,min(a[0],b[0])-margin),max(0,min(a[1],b[1])-margin),max(a[2],b[2])+margin,max(a[3],b[3])+margin);tailset=set(tail)
   def allowed(node):
    if node in remaining or node==source:
     if node!=attachment:return False
    x0,y0,x1,y1=struct.unpack_from('<4H',boxes,8*node)
    spatial=node in tailset or node==attachment or (window[0]<=x0 and window[1]<=y0 and x1<=window[2] and y1<=window[3])
    return spatial and owners[node]<struct.unpack_from('<H',resources,16*node+2)[0]
   ans=search(adjacency,allowed,attachment,sink,{},p['maximum_expanded_per_sink']);step={'task':int(task['id']),'attachment':attachment,'downstream_sinks':downstream[sink],'old_tail_nodes':len(tail),'old_tail_delay':old_delay,**{k:v for k,v in ans.items() if k!='path_nodes'}};record['steps'].append(step)
   if ans['status']=='optimal_additive_delay_path' and ans['delay']<old_delay and ans['hops']<=len(tail):
    path=ans['path_nodes'];trial=remaining.copy()
    for u,v in zip(path,path[1:]):assert v not in trial;trial[v]=u
    for target in sinks:
     seen=set();v=target
     while v!=source:assert v in trial and v not in seen;seen.add(v);v=trial[v]
    parent=trial;record['accepted_private_branches']+=1;step['private_branch_replaced']=True
   else:step['private_branch_replaced']=False
   save()
  if record['accepted_private_branches']:
   tree=folder/'candidate.route_trees.csv'
   with tree.open('x') as f:
    w=csv.DictWriter(f,fieldnames=['net_id','source','parent','child']);w.writeheader()
    for row in allrows:
     if int(row['net_id'])!=net:w.writerow(row)
    w.writerows({'net_id':net,'source':source,'parent':u,'child':v} for v,u in sorted(parent.items()))
   record.update(candidate_tree=str(tree),candidate_tree_sha256=sha(tree),status='complete_private_tree_requires_native_validation')
  else:record['status']='no_improving_private_tail_found'
  record['wall_ns']=time.monotonic_ns()-start;save()
 for m in maps:m.close()
 for f in handles:f.close()
 state['status']='tail_probes_terminal_requires_independent_review';save()
if __name__=='__main__':main()
