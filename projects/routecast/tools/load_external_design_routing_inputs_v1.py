"""Graph-affine static prices plus exact current-layout timing; no legacy fallback."""
import json,sys
from pathlib import Path
from array import array
from types import MappingProxyType
from pre_route_endpoints import sha
from load_external_current_initial_timing_v1 import load as load_timing

def load(endpoint_path,node_base_proof,criticality_directory,n,scale):
 endpoint_path=Path(endpoint_path).resolve();node_base_proof=Path(node_base_proof).resolve();criticality_directory=Path(criticality_directory).resolve();e=json.loads(endpoint_path.read_text());v=json.loads(node_base_proof.read_text());bindings={str(endpoint_path):sha(endpoint_path),str(node_base_proof):sha(node_base_proof)}
 if v.get('status')!='ALL119878_GRAPH_NODE_BASE_GROUPS_FLOAT32_CEIL_AND_ZERO_QUADRATIC_FANOUT_GUARD_VERIFIED':raise ValueError('unsupported external node-base admission')
 if (v.get('nodes'),v.get('scale'),v.get('array_byteorder'))!=(n,scale,sys.byteorder):raise ValueError('node-base shape/scale/byteorder mismatch')
 if not all(v.get(k) is True for k in ['all_native_base_equal_saved','all_native_T_quadratic_zero','ceil_error_less_than_one_lattice_unit']):raise ValueError('missing static price/fanout proof')
 if e.get('graph_sha256')!=v.get('graph_sha256') or e['inputs']['graph']['sha256']!=v['graph_sha256']:raise ValueError('graph/node-price epoch mismatch')
 for spec in e['inputs'].values():
  if sha(spec['path'])!=spec['sha256']:raise ValueError('endpoint input drift')
 for p,h in v['bindings'].items():
  if sha(p)!=h:raise ValueError('node-price source drift')
  bindings[p]=h
 payload=node_base_proof.parent/'node_base.u64'
 if v['bindings'].get(str(payload))!=sha(payload):raise ValueError('unbound node-price payload')
 values=array('Q');values.frombytes(payload.read_bytes())
 if values.itemsize!=8 or len(values)!=n:raise ValueError('node-price payload shape')
 # The node-base capture timing tag is provenance. T_quadratic0 and base=saved
 # establish graph-static prices, while each layout must supply its OWN timing.
 current=load_timing(criticality_directory,endpoint_path);normalized={}
 for q in e['connections']:
  cid=q['connection_id'];c=current[cid]
  if (c['endpoint_net_id'],c['source_rr'],c['target_rr'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('current CID/endpoint mismatch')
  normalized[cid]=MappingProxyType(dict(c,net=c['endpoint_net_id']))
 if set(normalized)!=set(current):raise ValueError('extra current timing CID')
 proof=criticality_directory/'verification.json';tv=json.loads(proof.read_text());bindings[str(proof)]=sha(proof);bindings.update(tv['bindings'])
 return tuple(values),MappingProxyType(normalized),bindings
