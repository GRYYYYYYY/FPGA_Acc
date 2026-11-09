"""Diagnose foreign owners on shorter private critical paths; publish no routing."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,struct
from occupied_tree_delay_search import search
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_blocked_critical_paths_20261020'
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
 parent=rows(p['candidate_tree']);baseline=rows(p['baseline_tree']);tasks={int(v['id']):v for v in rows(p['connections'])};by_net=collections.defaultdict(set);owners=collections.defaultdict(set)
 for row in parent:
  n=int(row['net_id'])
  for k in ['source','parent','child']:v=int(row[k]);by_net[n].add(v);owners[v].add(n)
 base_nodes=collections.defaultdict(set)
 for row in baseline:
  for k in ['source','parent','child']:base_nodes[int(row['net_id'])].add(int(row[k]))
 handles=[open(p[k],'rb') for k in ['nodes','edges','resources','boxes']];maps=[mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) for f in handles];nodes,edges,resources,boxes=maps;results=[]
 def adjacency(u):
  begin,count,_=struct.unpack_from('<IHH',nodes,8*u)
  for e in range(begin,begin+count):v,_,w=struct.unpack_from('<IHH',edges,8*e);yield v,w
 for task in p['critical_tasks']:
  t=tasks[task];source=int(t['source']);sink=int(t['sink']);net=int(t['net_id']);a=struct.unpack_from('<4H',boxes,8*source);b=struct.unpack_from('<4H',boxes,8*sink);margin=p['box_margin'];window=(max(0,min(a[0],b[0])-margin),max(0,min(a[1],b[1])-margin),max(a[2],b[2])+margin,max(a[3],b[3])+margin);exempt=by_net[net]|base_nodes[net]
  def allowed(node):
   x0,y0,x1,y1=struct.unpack_from('<4H',boxes,8*node)
   return node in exempt or (window[0]<=x0 and window[1]<=y0 and x1<=window[2] and y1<=window[3])
  answer=search(adjacency,allowed,source,sink,{},p['maximum_expanded_per_sink']);r={'task':task,'net':net,**answer}
  if 'path_nodes' in answer:
   conflicts=[]
   for v in answer['path_nodes']:
    foreign=owners[v]-{net};capacity=struct.unpack_from('<H',resources,16*v+2)[0]
    if len(foreign)>=capacity:conflicts.append({'node':v,'capacity':capacity,'foreign_owners':sorted(foreign)})
   r.update(conflicts=conflicts,foreign_conflicting_nets=sorted(set(n for v in conflicts for n in v['foreign_owners'])),capacity_legal=not conflicts)
  results.append(r)
 for m in maps:m.close()
 for f in handles:f.close()
 result={'status':'private_critical_path_foreign_conflicts_diagnosed','paths':results,'source_sha256':{str(D/'protocol.json'):sha(D/'protocol.json')},'scope':'Foreign occupancy deliberately ignored in candidate generation; list blockers against frozen parent. Paths may be capacity-invalid and are not published. Restricted box includes both original and baseline net nodes; no global shortest-path or native timing guarantee.','research_complete':False,'adopted':False}
 with (D/'result.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in a.items() if k not in ['path_nodes','conflicts']} for a in results]))
if __name__=='__main__':main()
