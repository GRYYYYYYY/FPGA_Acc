"""Private critical-path and named-blocker exchanges; no partial publication."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,os,struct,time
from occupied_tree_delay_search import search
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_local_exchange_20261020'
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
 tasks={int(v['id']):v for v in rows(p['connections'])};by_net=collections.defaultdict(list)
 for t in tasks.values():by_net[int(t['net_id'])].append(t)
 original=collections.defaultdict(dict);sources={}
 for v in rows(p['candidate_tree']):n=int(v['net_id']);original[n][int(v['child'])]=int(v['parent']);sources[n]=int(v['source'])
 def nodes(net,tree):return set(tree)|set(tree.values())|{sources[net]}
 original_nodes={n:nodes(n,t) for n,t in original.items()};native={int(v['task_id']):int(v['criticality_q']) for v in rows(p['native_parent_observations'])};diagnosis=json.loads(Path(p['blocked_paths']).read_text());paths={a['task']:a for a in diagnosis['paths']}
 handles=[open(p[k],'rb') for k in ['nodes','edges','resources','boxes']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nd,ed,res,box=maps
 def adjacency(u):
  begin,count,_=struct.unpack_from('<IHH',nd,8*u)
  for e in range(begin,begin+count):v,_,w=struct.unpack_from('<IHH',ed,8*e);yield v,w
 state={'status':'local_exchange_searches_running','pid':os.getpid(),'arms':[],'research_complete':False,'adopted':False}
 def save():
  t=D/'manifest.tmp';t.write_text(json.dumps(state,indent=2)+'\n');t.replace(D/'manifest.json')
 assert not (D/'manifest.json').exists();save()
 for arm in p['arms']:
  start=time.monotonic_ns();critical=paths[arm['task']];net=critical['net'];work={net,*arm['order']};assert set(arm['order'])==set(critical['foreign_conflicting_nets']);private={n:t.copy() for n,t in original.items()};record={'name':arm['name'],'critical_task':arm['task'],'blocker_order':arm['order'],'steps':[]};state['arms'].append(record);save()
  target=private[net]
  for u,v in zip(critical['path_nodes'],critical['path_nodes'][1:]):target[v]=u
  kept={}
  for task in by_net[net]:
   v=int(task['sink']);seen=set()
   while v!=sources[net]:assert v not in seen and v in target;seen.add(v);kept[v]=target[v];v=target[v]
  private[net]=kept;owners=collections.Counter()
  for n,t in private.items():
   if n not in work or n==net:owners.update(nodes(n,t))
  complete=True
  for n in arm['order']:
   source=sources[n];parent={};step={'net':n,'sink_searches':[]};record['steps'].append(step)
   for task in sorted(by_net[n],key=lambda t:(-native[int(t['id'])],int(t['id']))):
    sink=int(task['sink']);a=struct.unpack_from('<4H',box,8*source);b=struct.unpack_from('<4H',box,8*sink);margin=p['box_margin'];window=(max(0,min(a[0],b[0])-margin),max(0,min(a[1],b[1])-margin),max(a[2],b[2])+margin,max(a[3],b[3])+margin)
    def allowed(v):
     x0,y0,x1,y1=struct.unpack_from('<4H',box,8*v)
     return (v in original_nodes[n] or v in parent or v==source or (window[0]<=x0 and window[1]<=y0 and x1<=window[2] and y1<=window[3])) and owners[v]<struct.unpack_from('<H',res,16*v+2)[0]
    ans=search(adjacency,allowed,source,sink,parent,p['maximum_expanded_per_sink']);step['sink_searches'].append({'task':int(task['id']),**{k:v for k,v in ans.items() if k!='path_nodes'}});save()
    if ans['status']!='optimal_additive_delay_path':complete=False;break
    assert ans['hops']<=int(task['max_hops'])
    for u,v in zip(ans['path_nodes'],ans['path_nodes'][1:]):assert v not in parent or parent[v]==u;parent[v]=u
   if not complete:break
   private[n]=parent;owners.update(nodes(n,parent))
  if complete:
   assert all(count<=struct.unpack_from('<H',res,16*v+2)[0] for v,count in owners.items())
   folder=D/arm['name'];folder.mkdir();tree=folder/'candidate.route_trees.csv'
   with tree.open('x') as f:
    w=csv.DictWriter(f,fieldnames=['net_id','source','parent','child']);w.writeheader()
    for n in sorted(private):
     for v,u in sorted(private[n].items()):w.writerow({'net_id':n,'source':sources[n],'parent':u,'child':v})
   record.update(status='complete_private_exchange_requires_native_validation',candidate_tree=str(tree),candidate_tree_sha256=sha(tree))
  else:record['status']='private_exchange_incomplete_no_publication'
  record['wall_ns']=time.monotonic_ns()-start;save()
 for m in maps:m.close()
 for f in handles:f.close()
 state['status']='four_local_exchange_arms_terminal_require_review';save()
if __name__=='__main__':main()
