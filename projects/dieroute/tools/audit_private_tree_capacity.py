"""Check explicit protocol tree allocations against their own capacity/topology inputs."""
from pathlib import Path
import array,collections,csv,hashlib,json,mmap,struct,sys

def main(directory):
 D=Path(directory).resolve();p=json.loads((D/'protocol.json').read_text());refs={}
 def sha(f):
  f=Path(f);h=hashlib.sha256(f.read_bytes()).hexdigest();refs[str(f)]=h;return h
 def rows(f):
  with Path(f).open() as s:return list(csv.DictReader(s))
 dies=array.array('H');dies.frombytes(Path(p['node_die']).read_bytes())
 if sys.byteorder!='little':dies.byteswap()
 tasks=collections.defaultdict(list)
 for t in rows(p['connections']):tasks[int(t['net_id'])].append((int(t['source']),int(t['sink'])))
 with open(p['resources'],'rb') as f:
  cap=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);assert len(cap)==16*len(dies)
  def inspect(path):
   trees=collections.defaultdict(dict);sources={}
   for t in rows(path):
    n,s,u,v=(int(t[k]) for k in ['net_id','source','parent','child']);assert 0<=u<len(dies) and 0<=v<len(dies);assert v not in trees[n];trees[n][v]=u;assert sources.setdefault(n,s)==s
   assert set(trees)==set(tasks);occupancy=collections.Counter()
   for n,parent in trees.items():
    source=sources[n];assert all(s==source for s,_ in tasks[n]);seen={source}
    for target in set(parent)|{v for _,v in tasks[n]}:
     pathset=set();v=target
     while v not in seen:assert v not in pathset and v in parent;pathset.add(v);v=parent[v]
     seen.update(pathset)
    occupancy.update(set(parent)|{source})
   over=[v for v,c in occupancy.items() if c>struct.unpack_from('<H',cap,16*v+2)[0]]
   return {'nets':len(trees),'tree_edges':sum(map(len,trees.values())),'layer_transitions':sum(dies[v]!=dies[u] for t in trees.values() for v,u in t.items()),'overused_resources':len(over),'all_sinks_and_nodes_reachable':True}
  baseline=inspect(p['baseline_tree']);candidate=inspect(p['candidate_tree']);cap.close()
 for f in [p[k] for k in ['baseline_tree','candidate_tree','resources','node_die','connections']]+[D/'protocol.json',Path(__file__).resolve()]:sha(f)
 result={'status':'explicit_protocol_tree_capacity_and_reachability_reviewed','baseline':baseline,'candidate':candidate,'source_sha256':refs,'scope':'Unique parents,root reachability,net-deduplicated capacity and model transitions only. Native edge/packedwiring legality and quality are separate requirements.','research_complete':False}
 with (D/'independent_preflight.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main(sys.argv[1])
