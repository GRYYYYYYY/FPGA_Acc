"""Original Expat XML proof of every exported relaxed reverse Bellman potential."""
import json,sys,hashlib,xml.parsers.expat
from array import array
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_budget_astar_reuse_warm_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');assert proof['status']=='ALL3_BUDGET_ASTAR_REUSE_WARM_FRAMES_AND_RAW_BOUND_CERTIFICATES_PREPARED';assert all(sha(p)==h for p,h in proof['bindings'].items());protocol=read(D/'protocol.json');mp=D/'remaining_delay_bounds/manifest.json';meta=read(mp);ep=read(protocol['cases'][0]['endpoint']);graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256']==ep['graph_sha256'];assert meta['scale']==10**18;types=[];caps=array('Q');us=array('Q');vs=array('Q');sw=array('Q');weights={};stack=[];active={};timings=0
 def start(name,attrs):
  nonlocal timings
  parent=stack[-1] if stack else None;stack.append(name)
  if name=='node' and parent=='rr_nodes':assert int(attrs['id'])==len(caps);types.append(attrs['type']);caps.append(int(attrs['capacity']))
  elif name=='timing' and parent=='node':assert Fraction(attrs['R'])==Fraction(attrs['C'])==0;timings+=1
  elif name=='switch' and parent=='switches':active['switch']=int(attrs['id'])
  elif name=='timing' and parent=='switch':
   assert all(Fraction(attrs.get(k,'0'))==0 for k in ['R','Cin','Cout','Cinternal']);w=Fraction(attrs.get('Tdel','0'))*10**18;assert w.denominator==1 and w>=0;weights[active['switch']]=w.numerator
  elif name=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']));sw.append(int(attrs['switch_id']))
 def end(name):assert stack.pop()==name
 parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 n,m=len(caps),len(us);assert timings==n and (n,m)==(meta['nodes'],meta['arcs']);bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'verification.json',D/'protocol.json',mp,graph]}
 def u64(path,count,byteorder):
  path=Path(path);assert path.stat().st_size==count*8;a=array('Q')
  with path.open('rb') as f:a.fromfile(f,count)
  assert byteorder in ['little','big']
  if byteorder!=sys.byteorder:a.byteswap()
  bindings[str(path)]=sha(path);return a
 offsets=u64(meta['row_offsets_file'],n+1,meta['csr_byteorder']);slots=u64(meta['slot_edge_ids_file'],m,meta['csr_byteorder']);assert offsets[0]==0 and offsets[-1]==m and all(a<=b for a,b in zip(offsets,offsets[1:]));seen=bytearray(m);dest=array('Q');raw=[]
 for u in range(n):
  for pos in range(offsets[u],offsets[u+1]):
   eid=slots[pos];assert eid<m and not seen[eid] and us[eid]==u;seen[eid]=1;dest.append(vs[eid]);raw.append(weights[sw[eid]])
 assert all(seen);digest=hashlib.sha256()
 for values in [offsets,dest]:
  a=array('Q',values)
  if meta['csr_byteorder']!=sys.byteorder:a.byteswap()
  digest.update(a.tobytes())
 for w in raw:digest.update(w.to_bytes(16,'little'))
 assert digest.hexdigest()==meta['context_sha256'];reverse_offsets=array('Q',[0])*(n+1)
 for v in vs:reverse_offsets[v+1]+=1
 for i in range(n):reverse_offsets[i+1]+=reverse_offsets[i]
 cursor=array('Q',reverse_offsets);reverse_edges=array('Q',[0])*m
 for eid,v in enumerate(vs):reverse_edges[cursor[v]]=eid;cursor[v]+=1
 keys=set();rows=[];direct_total=trivial_total=0
 for index,b in enumerate(meta['bounds']):
  target,cap=b['target'],b['cap'];assert (target,cap) not in keys and 0<=target<n and type(cap) is int and cap>0;keys.add((target,cap));p=Path(b['path']);assert sha(p)==b['sha256']
  if b['encoding']=='NATIVE_ENDIAN_U64':phi=u64(p,n,b['byteorder'])
  else:assert b['encoding']=='JSON_INTEGERS';phi=read(p);assert len(phi)==n and all(type(v) is int and v>=0 for v in phi)
  assert max(phi)<=cap and phi[target]==0;direct=0
  for v,value in enumerate(phi):
   if value==cap:continue
   for pos in range(reverse_offsets[v],reverse_offsets[v+1]):
    eid=reverse_edges[pos];assert phi[us[eid]]<=weights[sw[eid]]+value;direct+=1
  # Heads at cap satisfy h(u)<=cap<=nonnegative_arc+cap analytically.
  trivial=m-direct;direct_total+=direct;trivial_total+=trivial;bindings[str(p)]=sha(p);rows.append(dict(target=target,cap=cap,original_arc_inequalities_directly_compared=direct,cap_head_arc_inequalities_analytically_certified=trivial,total_original_arcs_certified=m))
  if index%20==0:print('RAW_BOUND_BELLMAN_CERTIFIED',index+1,'of',len(meta['bounds']),flush=True)
 assert len(keys)==meta['cache_misses'];assert all(sha(p)==h for p,h in bindings.items());(D/'remaining_bounds_independent_verification_v1.json').write_text(json.dumps(dict(status='ALL_EXPORTED_RELAXED_RAW_BOUNDS_ORIGINAL_XML_BELLMAN_CERTIFIED',graph_sha256=meta['graph_sha256'],context_sha256=meta['context_sha256'],nodes=n,arcs=m,bounds=len(rows),rows=rows,direct_arc_comparisons=direct_total,analytic_cap_head_arc_proofs=trivial_total,total_arc_inequalities_certified=direct_total+trivial_total,bindings=bindings,scope='Every relaxed original arc inequality h(u)<=raw+h(v) with sink0 certified, either direct comparison or bounded nonnegative cap-head implication. Telescoping proves admissible remaining raw delay for any more restricted frozen-tree path; raw lower bound also lower-bounds nonnegative novelty objective. Does not require every value to be exact distance, does not prove unreachability, same tie paths or speedup.'),indent=2)+'\n');print('PASS',len(rows),'bounds',direct_total,'direct',trivial_total,'analytic')
if __name__=='__main__':main()
