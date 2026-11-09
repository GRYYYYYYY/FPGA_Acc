"""Reconstruct all frozen restore trees and check sinks, occupancy and layer transitions."""
from pathlib import Path
import array,collections,csv,hashlib,json,mmap,struct,sys
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_alternative_chain_probe_20261020/native_check'
def rows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def main():
 p=json.loads((D/'protocol.json').read_text());base=rows(p['baseline_tree']);candidate=rows(p['candidate_tree']);label='elliptic_28x22_cw320_seed1'
 topo=R/'work/width_coverage_roundtrip_20261017'/label/'topology.node_die';res=R/'work/width_coverage_native_costs_20261018'/label/'input.resources';connections=topo.parent/'connections.csv'
 dies=array.array('H');dies.frombytes(topo.read_bytes())
 if sys.byteorder!='little':dies.byteswap()
 tasks=collections.defaultdict(list)
 for v in rows(connections):tasks[int(v['net_id'])].append((int(v['source']),int(v['sink'])))
 def inspect(values):
  trees={};sources={}
  for v in values:
   n,s,u,c=(int(v[k]) for k in ['net_id','source','parent','child']);assert 0<=u<len(dies) and 0<=c<len(dies)
   assert c not in trees.setdefault(n,{});trees[n][c]=u;assert sources.setdefault(n,s)==s
  owners=collections.Counter()
  for n,tree in trees.items():
   s=sources[n];assert all(src==s for src,_ in tasks[n]);seen={s}
   for sink in set(tree)|{sink for _,sink in tasks[n]}:
    path=set();v=sink
    while v not in seen:
     assert v not in path and v in tree,('cycle_or_disconnected',n,v);path.add(v);v=tree[v]
    seen.update(path)
   owners.update(set(tree)|{s})
  with res.open('rb') as f:
   m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);assert len(m)==16*len(dies)
   over=[{'node':v,'nets':count,'capacity':struct.unpack_from('<H',m,16*v+2)[0]} for v,count in owners.items() if count>struct.unpack_from('<H',m,16*v+2)[0]];m.close()
  return {'nets':len(trees),'tree_edges':sum(map(len,trees.values())),'layer_transitions':sum(dies[u]!=dies[v] for t in trees.values() for v,u in t.items()),'overused_resources':len(over),'overuse_examples':over[:20],'all_tree_nodes_and_sinks_reachable':True}
 baseline=inspect(base);parent=inspect(candidate);arms=[]
 for arm in p['arms']:
  nets=set(arm['nets']);values=[v for v in candidate if int(v['net_id']) not in nets]+[v for v in base if int(v['net_id']) in nets];a=inspect(values);a.update(name=arm['name'],restored_nets=arm['nets']);arms.append(a)
 files=[D/'protocol.json',Path(p['baseline_tree']),Path(p['candidate_tree']),topo,res,connections,Path(__file__).resolve()]
 def sha(f):
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  return h.hexdigest()
 result={'status':'distinct_shared_chain_capacity_preflight_reviewed','baseline':baseline,'parent':parent,'arms':arms,'source_sha256':{str(f):sha(f) for f in files},'scope':'Exact whole-net mixtures reconstructed from frozen inputs. Reachability, unique parents, net-deduplicated occupancy and modeled layer transitions only; native directed-edge legality and STA are separate requirements. All conflicts retained; no physical SLL or adoption claim.','research_complete':False,'adopted':False}
 with (D/'independent_preflight.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))
if __name__=='__main__':main()
