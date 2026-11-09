"""Protocol-driven private exchanges with per-net shared-crossing caps."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,os,struct,sys,time
from sparse_delay_capped_search import search as delay_search
from sparse_crossing_first_search import search as crossing_search
D=Path(sys.argv[1]).resolve()
def rows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((D/'protocol.json').read_text());search=delay_search if p['search_objective']=='delay' else crossing_search
 for f,h in p['source_sha256'].items():assert sha(f)==h,f
 tasks={int(t['id']):t for t in rows(p['connections'])};by_net=collections.defaultdict(list)
 for t in tasks.values():by_net[int(t['net_id'])].append(t)
 original=collections.defaultdict(dict);sources={}
 for t in rows(p['candidate_tree']):n=int(t['net_id']);sources[n]=int(t['source']);original[n][int(t['child'])]=int(t['parent'])
 observations={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in rows(p['native_parent_observations'])};criticality={t:v['criticality_q'] for t,v in observations.items()};paths={a['task']:a for a in json.loads(Path(p['blocked_paths']).read_text())['paths']}
 handles=[open(p[k],'rb') for k in ['nodes','edges','resources','boxes','node_die']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nd,ed,res,boxes,dies=maps
 def die(v):return struct.unpack_from('<H',dies,2*v)[0]
 def cross(t):return sum(die(u)!=die(v) for v,u in t.items())
 def occupied(n,t):return set(t)|set(t.values())|{sources[n]}
 oldnodes={n:occupied(n,t) for n,t in original.items()};caps={n:cross(t) for n,t in original.items()}
 state={'status':'budgeted_local_exchanges_running','pid':os.getpid(),'arms':[],'research_complete':False,'adopted':False}
 def save():
  t=D/'manifest.tmp';t.write_text(json.dumps(state,indent=2)+'\n');t.replace(D/'manifest.json')
 assert not (D/'manifest.json').exists();save()
 for arm in p['arms']:
  start=time.monotonic_ns();target=int(tasks[arm['task']]['net_id']);work={target,*arm['order']};assert set(arm['order'])==set(paths[arm['task']]['foreign_conflicting_nets']);private={n:t.copy() for n,t in original.items()};owners=collections.Counter()
  for n,t in original.items():
   if n not in work:owners.update(occupied(n,t))
  record={'name':arm['name'],'target':target,'steps':[]};state['arms'].append(record);save();complete=True
  pool_left=p['global_crossing_cap']-sum(caps[k] for k in original if k not in work)
  build_order=[target,*arm['order']]
  for position,n in enumerate(build_order):
   reserve=sum(len({die(sources[k]),*(die(int(t['sink'])) for t in by_net[k])})-1 for k in build_order[position+1:])
   net_cap=pool_left-reserve
   if net_cap<0:complete=False;record['budget_reservation_failed']=True;break
   source=sources[n];parent={};step={'net':n,'crossing_cap':net_cap,'pool_left_before':pool_left,'reserved_future_minimum':reserve,'searches':[]};record['steps'].append(step)
   ordered=sorted(by_net[n],key=lambda t:(0 if int(t['id'])==arm['task'] else 1,-criticality[int(t['id'])],int(t['id'])))
   attempted_orders=set();step['failed_attempts']=[]
   for attempt in range(p['maximum_net_order_attempts']):
    key=tuple(int(t['id']) for t in ordered)
    if key in attempted_orders:complete=False;step['repeat_order_stop']=True;break
    attempted_orders.add(key);parent={};step['searches']=[];complete=True
    for task in ordered:
     sink=int(task['sink']);a=struct.unpack_from('<4H',boxes,8*source);b=struct.unpack_from('<4H',boxes,8*sink);margin=p['box_margin'];window=(max(0,min(a[0],b[0])-margin),max(0,min(a[1],b[1])-margin),max(a[2],b[2])+margin,max(a[3],b[3])+margin)
     def allowed(v):
      x0,y0,x1,y1=struct.unpack_from('<4H',boxes,8*v)
      return (v in oldnodes[n] or v in parent or v==source or (window[0]<=x0 and window[1]<=y0 and x1<=window[2] and y1<=window[3])) and owners[v]<struct.unpack_from('<H',res,16*v+2)[0]
     def adjacency(u):
      begin,count,_=struct.unpack_from('<IHH',nd,8*u)
      for e in range(begin,begin+count):
       v,_,delay=struct.unpack_from('<IHH',ed,8*e);yield v,delay,int(die(u)!=die(v) and v not in parent)
     before=cross(parent);ans=search(adjacency,allowed,source,sink,parent,net_cap-before,p['maximum_expanded_per_sink'],delay_budget=max(0,observations[int(task['id'])]['delay_ps']+p['baseline_cpd_ps']+observations[int(task['id'])]['slack_ps']));step['searches'].append({'task':int(task['id']),**{k:v for k,v in ans.items() if k!='path_nodes'}});save()
     if ans['status']!='optimal_bounded_delay_path':complete=False;break
     if ans['hops']>int(task['max_hops']):complete=False;step['hop_guard_failed']=True;break
     for u,v in zip(ans['path_nodes'],ans['path_nodes'][1:]):assert v not in parent or parent[v]==u;parent[v]=u
     assert cross(parent)==before+ans['crossings']<=net_cap
    if complete:break
    step['failed_attempts'].append({'attempt':attempt,'order':list(key),'searches':step['searches'].copy()})
    failed=step['searches'][-1]['task'];priority=[t for t in ordered if int(t['id'])==failed];rest=[t for t in ordered if int(t['id'])!=failed]
    if n==target:
     if failed==arm['task']:break
     critical=[t for t in rest if int(t['id'])==arm['task']];rest=[t for t in rest if int(t['id'])!=arm['task']];ordered=critical+priority+rest
    else:ordered=priority+rest
    save()
   if not complete:break
   private[n]=parent;owners.update(occupied(n,parent));step['final_crossings']=cross(parent);pool_left-=cross(parent)
  if complete:
   assert all(c<=struct.unpack_from('<H',res,16*v+2)[0] for v,c in owners.items());assert sum(map(cross,private.values()))<=p['global_crossing_cap'];folder=D/arm['name'];folder.mkdir();tree=folder/'candidate.route_trees.csv'
   with tree.open('x') as f:
    w=csv.DictWriter(f,fieldnames=['net_id','source','parent','child']);w.writeheader()
    for n,t in sorted(private.items()):
     for v,u in sorted(t.items()):w.writerow({'net_id':n,'source':sources[n],'parent':u,'child':v})
   record.update(status='complete_budgeted_exchange_requires_native_validation',candidate_tree=str(tree),candidate_tree_sha256=sha(tree))
  else:record['status']='budgeted_private_exchange_incomplete_no_publication'
  record['wall_ns']=time.monotonic_ns()-start;save()
 for m in maps:m.close()
 for f in handles:f.close()
 state['status']='budgeted_exchange_arms_terminal_require_review';save()
if __name__=='__main__':main()
