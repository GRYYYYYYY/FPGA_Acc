"""Explicit per-design routing inputs; authenticate identity before model execution."""
import json,struct
from pathlib import Path
from pre_route_endpoints import sha
from load_initial_connection_criticalities_v1 import load as load_criticalities

def load(endpoint_path,node_base_proof,criticality_directory,n,scale):
 endpoint_path=Path(endpoint_path).resolve();node_base_proof=Path(node_base_proof).resolve()
 criticality_directory=Path(criticality_directory).resolve()
 criticality_proof=criticality_directory/'verification.json'
 endpoint_hash=sha(endpoint_path);endpoint=json.loads(endpoint_path.read_text())
 bindings={str(endpoint_path):endpoint_hash};proofs=[]
 for path in (node_base_proof,criticality_proof):
  proof=json.loads(path.read_text())
  if proof.get('bindings',{}).get(str(endpoint_path))!=endpoint_hash:
   raise ValueError('proof does not bind requested endpoint snapshot')
  proofs.append(proof);bindings[str(path)]=sha(path)
  for source,digest in proof['bindings'].items():
   if source in bindings and bindings[source]!=digest:raise ValueError('conflicting source bindings')
   bindings[source]=digest
 base=proofs[0]
 if (base.get('nodes'),base.get('scale'),base.get('payload_format'))!=(n,scale,'unsigned128_little_endian'):
  raise ValueError('node-base domain, scale or payload format mismatch')
 if not base.get('all_original_node_ids_types_segments_and_native_group_counts_pass'):
  raise ValueError('node-base admission missing')
 if base.get('payload_file')!='node_base.u128le':raise ValueError('unexpected payload filename')
 path=node_base_proof.parent/'node_base.u128le'
 if str(path) not in base['bindings']:raise ValueError('unbound node-base payload')
 for spec in endpoint['inputs'].values():
  if sha(spec['path'])!=spec['sha256']:raise ValueError('endpoint input changed')
 if endpoint['graph_sha256']!=endpoint['inputs']['graph']['sha256']:
  raise ValueError('endpoint graph identity mismatch')
 if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('input proof binding changed')
 payload=path.read_bytes()
 if len(payload)!=16*n:raise ValueError('node-base payload domain mismatch')
 values=tuple(lo+(hi<<64) for lo,hi in struct.iter_unpack('<QQ',payload));del payload
 if any(v>=2**120 for v in values):raise ValueError('node-base exceeds cost domain')
 criticalities=load_criticalities(criticality_directory)
 seen=set()
 for q in endpoint['connections']:
  cid=q['connection_id']
  if cid in seen or cid not in criticalities:raise ValueError('connection ID domain mismatch')
  seen.add(cid);c=criticalities[cid]
  if (q['net_id'],q['source'],q['sink'])!=(c['net'],c['source_rr'],c['target_rr']):
   raise ValueError('criticality endpoint identity mismatch')
 if seen!=set(criticalities):raise ValueError('extra criticality connections')
 if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('inputs changed during load')
 return tuple(values),criticalities,bindings
