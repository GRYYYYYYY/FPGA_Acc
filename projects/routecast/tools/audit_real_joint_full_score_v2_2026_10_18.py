"""Full positive RR-domain joint replay against previously verified vectors."""
import hashlib,json,time,xml.etree.ElementTree as ET
from array import array
from pathlib import Path
from joint_full_score_state_v1 import Joint

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/real_joint_full_score_v2_2026-10-18');out.mkdir(exist_ok=False)
 root=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');gp=root/'groups.json';g=json.loads(gp.read_text());config=json.loads((root/'protocol.json').read_text());case='case_01';methods=['native_retained_off','native_retained_on'];keys=[(c,m) for c in ['case_01','case_02','case_03'] for m in methods];sequence=[1,3,2,4,5,3,1,0];inputs=config['inputs'][case]
 ep=Path(inputs['endpoint']);endpoint=json.loads(ep.read_text());graph=Path(endpoint['inputs']['graph']['path']);assert sha(graph)==g['graph_sha256']
 vp=Path('experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json');proof=json.loads(vp.read_text());assert proof['status']=='pass'
 manifest_path=root/'vector_manifest.json';manifest=json.loads(manifest_path.read_text());groups={i:v['members'] for i,v in enumerate(g['groups'])};sinkgroups={v['sink_RR']:i for i,v in enumerate(g['groups']) if v['kind']=='direct_sink_IPIN'};sources={int(n) for n,reason in g['fallback_reasons'].items() if reason=='fixed_or_unsupported_type_SOURCE'}
 sourcepaths=[Path(__file__),Path('tools/joint_full_score_state_v1.py'),Path('tools/incremental_IPIN_feature_cache_v1.py'),Path('tools/incremental_NET_group_ownership_v1.py'),Path('tools/net_group_collision_risk_v1.py')]
 paths=[gp,root/'protocol.json',graph,ep,vp,manifest_path,*sourcepaths]
 for case,method in keys:
  paths.append(Path(config['inputs'][case]['endpoint']))
  paths.append(Path(config['inputs'][case]['predictions'][method]))
  for family in ['typed_group_mean','typed_NET_collision']:paths.append(Path(manifest[case+'__'+method+'__'+family]['path']))
 bindings={str(p.resolve()):sha(p) for p in paths}
 for path in paths:
  name=str(path.resolve())
  if path not in sourcepaths and path not in [Path(v['endpoint']) for v in config['inputs'].values()]+[vp,manifest_path,root/'protocol.json']:assert proof['bindings'][name]==bindings[name]
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,states=keys,sequence=sequence,fields=['typed_group_mean','typed_NET_collision'],domain='All904438 positive RR nodes including fixed fallback capacity normalization',scope='Existing exposed development case, serial combined bookkeeping, not forecast gate or native utility promotion'),f,indent=2)
 starts=array('I');dest=array('I');caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2] if len(stack)>1 else None
  if e.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(e.get('id'));cap=int(e.get('capacity'))
   if cap>0:caps[n]=cap
   parent.remove(e);e.clear()
  elif e.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   starts.append(int(e.get('src_node')));dest.append(int(e.get('sink_node')));parent.remove(e);e.clear()
  stack.pop()
 assert list(caps)==g['positive_RR_ids'] and len(caps)==904438 and len(dest)==8097539
 print('FULL DOMAIN XML VERIFIED',len(caps),len(dest),flush=True)
 def project(key):
  case,method=key;inputs=config['inputs'][case];endpoint=json.loads(Path(inputs['endpoint']).read_text());assert endpoint['graph_sha256']==g['graph_sha256']
  frame=json.loads(Path(inputs['predictions'][method]).read_text());assert frame['graph_sha256']==g['graph_sha256'];records=[]
  for r in frame['records']:
   node=r['source'];nodes={node}
   for edge in r['answer']['physical_edge_ids']:
    assert type(edge) is int and 0<=edge<len(dest) and starts[edge]==node
    node=dest[edge];nodes.add(node)
   assert node==r['sink'] and nodes<=caps.keys()
   records.append({**{k:r[k] for k in ['connection_id','net_id','source','sink']},'nodes':sorted(nodes)})
  records.sort(key=lambda r:r['connection_id']);assert len(records)==115572
  assert [{k:r[k] for k in ['connection_id','net_id','source','sink']} for r in records]==sorted(endpoint['connections'],key=lambda r:r['connection_id'])
  return records
 snapshots=[project(key) for key in keys];a=snapshots[0]
  # Archive an authenticated original-XML edge index for later stage reuse.
 index={}
 for name,data in [('edge_source',starts),('edge_destination',dest),('positive_capacity',array('I',caps.values()))]:
  path=out/(name+'.u32')
  with path.open('xb') as f:data.tofile(f)
  index[name]=dict(path=str(path.resolve()),sha256=sha(path),values=len(data),typecode=data.typecode,itemsize=data.itemsize)
 import sys
 with (out/'graph_index.json').open('x') as f:json.dump(dict(graph_sha256=g['graph_sha256'],byteorder=sys.byteorder,positive_ids_binding=bindings[str(gp.resolve())],arrays=index),f,indent=2)
 t=time.perf_counter();state=Joint(g['graph_sha256'],groups,sinkgroups,sources,caps,a);initial=time.perf_counter()-t
 print('JOINT FULL DOMAIN INITIALIZED',initial,flush=True)
 comparisons=0
 def verify(view,key,rows):
  nonlocal comparisons
  case,method=key
  assert view.component_generations==(view.generation,view.generation)
  for r in rows:assert view.query(r['connection_id'])==r
  vectors=[]
  for family in ['typed_group_mean','typed_NET_collision']:
   item=manifest[case+'__'+method+'__'+family];assert sha(item['path'])==item['sha256'];v=array('d');v.frombytes(Path(item['path']).read_bytes());assert len(v)==len(caps);vectors.append(v)
  for i,n in enumerate(g['positive_RR_ids']):assert view.score(n)==(vectors[0][i],vectors[1][i]),(method,n)
  comparisons+=2*len(caps)
 verify(state.view(),keys[0],a);results=[];current=0
 for target in sequence:
  old,new=snapshots[current],snapshots[target];oldkey,key=keys[current],keys[target]
  delta=[dict(old=x,new=y) for x,y in zip(old,new) if x!=y];view=state.view();t=time.perf_counter();receipt=state.commit(state.prepare(g['graph_sha256'],view.generation,delta));elapsed=time.perf_counter()-t
  verify(view,oldkey,old);verify(state.view(),key,new);results.append(dict(before=oldkey,target=key,query_updates=len(delta),supplied_delta_prepare_commit_seconds=elapsed,receipt=receipt));current=target;print('FULL VECTOR REPLAY PASS',oldkey,'->',key,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings={**bindings,str((out/'graph_index.json').resolve()):sha(out/'graph_index.json')},states=keys,sequence=sequence,positive_RR_nodes=len(caps),queries_per_frame=len(a),initial_construction_seconds=initial,full_score_values_checked=comparisons,transitions=results,scope='Complete typed mean/collision score vectors and every query projection match previously independently verified vectors; predecessor views retained, serial publication only. Cost excludes path/graph projection, file IO, delta discovery and predecessor release. No original quality/native utility promotion.'),f,indent=2)
 print('REAL JOINT FULL SCORE AUDIT PASS',comparisons,flush=True)
if __name__=='__main__':main()
