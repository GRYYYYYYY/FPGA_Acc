"""Private occupied-resource-aware additive-delay net rerouting probes."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,os,struct,time
from occupied_tree_delay_search import search
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_occupied_net_probe_20261020'
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
 assert not (D/'manifest.json').exists();state={'status':'private_net_search_running','pid':os.getpid(),'probes':[],'research_complete':False,'adopted':False}
 def save():
  tmp=D/'manifest.tmp';tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(D/'manifest.json')
 save();allrows=rows(p['candidate_tree']);by_net=collections.defaultdict(list)
 for row in allrows:by_net[int(row['net_id'])].append(row)
 tasks=rows(p['connections']);timing={int(v['task_id']):int(v['criticality_q']) for v in rows(p['timing'])}
 handles=[open(p[k],'rb') for k in ['nodes','edges','resources']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nodes,edges,resources=maps
 def adjacency(u):
  start,count,_=struct.unpack_from('<IHH',nodes,8*u)
  for e in range(start,start+count):
   v,_,delay=struct.unpack_from('<IHH',edges,8*e);yield v,delay
 for net in p['nets']:
  start=time.monotonic_ns();folder=D/('net_'+str(net));folder.mkdir();record={'net':net,'steps':[]};state['probes'].append(record);save()
  owners=collections.Counter()
  for other,values in by_net.items():
   if other!=net:owners.update({int(v[k]) for v in values for k in ['source','parent','child']})
  def allowed(node):return owners[node]<struct.unpack_from('<H',resources,16*node+2)[0]
  selected=sorted([v for v in tasks if int(v['net_id'])==net],key=lambda v:(-timing[int(v['id'])],int(v['id'])))
  source=int(selected[0]['source']);parent={};complete=True
  for task in selected:
   answer=search(adjacency,allowed,source,int(task['sink']),parent,p['maximum_expanded_per_sink']);record['steps'].append({'task':int(task['id']),**{k:v for k,v in answer.items() if k!='path_nodes'}});save()
   if answer['status']!='optimal_additive_delay_path':complete=False;break
   path=answer['path_nodes'];assert len(path)-1<=int(task['max_hops'])
   for u,v in zip(path,path[1:]):assert v not in parent or parent[v]==u;parent[v]=u
  record['complete']=complete
  if complete:
   tree=folder/'candidate.route_trees.csv'
   with tree.open('x') as stream:
    w=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);w.writeheader()
    for row in allrows:
     if int(row['net_id'])!=net:w.writerow(row)
    w.writerows({'net_id':net,'source':source,'parent':u,'child':v} for v,u in sorted(parent.items()))
   record.update(candidate_tree=str(tree),candidate_tree_sha256=sha(tree),status='private_complete_tree_requires_native_check')
  else:record['status']='private_search_failed_no_state_published'
  record['wall_ns']=time.monotonic_ns()-start;save()
 for m in maps:m.close()
 for f in handles:f.close()
 state['status']='both_private_net_probes_terminal_require_review';save()
if __name__=='__main__':main()
