"""Versioned graph-static price/current-frame timing adapter for all3 widths."""
import json,sys
from array import array
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
from load_prince_current_initial_timing_v1 import load as load_timing

def load(endpoint_path,node_base_proof,criticality_directory,n,scale,*,expected_timing_epoch=None):
 ep=Path(endpoint_path).resolve();bp=Path(node_base_proof).resolve();td=Path(criticality_directory).resolve();e=json.loads(ep.read_text());v=json.loads(bp.read_text());bindings={str(ep):sha(ep),str(bp):sha(bp)}
 def add(path,digest):
  if path in bindings and bindings[path]!=digest:raise ValueError('conflicting bound input')
  bindings[path]=digest
 if v.get('schema')!='ROUTECAST_GRAPH_STATIC_NODE_BASE_V2' or v.get('status')!='GRAPH_NATIVE_INDEXED_GROUPS_XML_PRICES_AND_STATIC_FANOUT_VERIFIED':raise ValueError('unsupported graph-static price proof')
 if type(n) is not int or type(scale) is not int or (v.get('nodes'),v.get('scale'),v.get('array_byteorder'))!=(n,scale,sys.byteorder):raise ValueError('node-price shape/scale/byteorder mismatch')
 if not all(v.get(k) is True for k in ['all_native_base_equal_saved','all_native_T_quadratic_zero','ceil_error_less_than_one_lattice_unit','graph_static_price_scope']):raise ValueError('static/fanout price guard missing')
 if e.get('graph_sha256')!=v.get('graph_sha256') or e['inputs']['graph']['sha256']!=v['graph_sha256']:raise ValueError('graph/price epoch mismatch')
 for spec in e['inputs'].values():
  if sha(spec['path'])!=spec['sha256']:raise ValueError('endpoint input drift')
  add(spec['path'],spec['sha256'])
 for p,h in v['bindings'].items():
  if sha(p)!=h:raise ValueError('price proof source drift')
  add(p,h)
 payload=bp.parent/'node_base.u64'
 if v['bindings'].get(str(payload))!=sha(payload):raise ValueError('unbound price payload')
 prices=array('Q');prices.frombytes(payload.read_bytes())
 if prices.itemsize!=8 or len(prices)!=n:raise ValueError('price array domain mismatch')
 current=load_timing(td,ep,expected_epoch=expected_timing_epoch);out={}
 for q in e['connections']:
  cid=q['connection_id'];c=current[cid]
  if cid in out or (c['endpoint_net_id'],c['source_rr'],c['target_rr'])!=(q['net_id'],q['source'],q['sink']):raise ValueError('current timing CID mismatch')
  if not 0<=q['source']<n or not 0<=q['sink']<n:raise ValueError('RR endpoint outside price domain')
  out[cid]=MappingProxyType(dict(c,net=c['endpoint_net_id']))
 if set(out)!=set(current):raise ValueError('extra timing CIDs')
 tp=td/'verification.json';tv=json.loads(tp.read_text());add(str(tp),sha(tp))
 for p,h in tv['bindings'].items():add(p,h)
 if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('inputs changed during load')
 return tuple(prices),MappingProxyType(out),bindings
