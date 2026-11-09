"""Remap one authenticated fixed timing epoch across a placement-only change."""
import json
from pathlib import Path
from types import MappingProxyType
from load_initial_connection_criticalities_v1 import load as load_initial
from pre_route_endpoints import sha

def remap(before_endpoint,after_endpoint,criticality_directory,before_manifest,after_manifest):
 paths=[Path(x).resolve() for x in [before_endpoint,after_endpoint,before_manifest,after_manifest]]
 before_endpoint,after_endpoint,before_manifest,after_manifest=paths
 bindings={str(p):sha(p) for p in paths}
 a=json.loads(before_endpoint.read_text());b=json.loads(after_endpoint.read_text())
 if a['graph_sha256']!=b['graph_sha256'] or a['inputs']['net']['sha256']!=b['inputs']['net']['sha256'] or a['net_names']!=b['net_names']:
  raise ValueError('requires fixed graph and packed-netlist identity')
 for ep in [a,b]:
  for spec in ep['inputs'].values():
   if sha(spec['path'])!=spec['sha256']:raise ValueError('endpoint input changed')
   bindings[spec['path']]=spec['sha256']
 def manifest(path,endpoint):
  rows={};pins=set()
  for line in path.read_text().splitlines():
   x=line.split()
   if x[0]!='Q':continue
   cid,net,pin,source,target=map(int,x[1:]);key=net,pin
   if cid in rows or key in pins:raise ValueError('duplicate manifest identity')
   rows[cid]=(net,pin,source,target);pins.add(key)
  queries={q['connection_id']:q for q in endpoint['connections']}
  if len(queries)!=len(endpoint['connections']) or set(queries)!=set(rows):raise ValueError('manifest coverage')
  for cid,(net,pin,source,target) in rows.items():
   q=queries[cid]
   if (q['net_id'],q['source'],q['sink'])!=(net,source,target):raise ValueError('manifest endpoint identity')
  return rows
 ma=manifest(before_manifest,a);mb=manifest(after_manifest,b)
 if set(ma)!=set(mb):raise ValueError('connection domain changed')
 old=load_initial(criticality_directory);proofpath=Path(criticality_directory).resolve()/'verification.json';proof=json.loads(proofpath.read_text())
 if proof['bindings'].get(str(before_endpoint))!=bindings[str(before_endpoint)]:raise ValueError('timing epoch not bound to before placement')
 bindings.update(proof['bindings']);bindings[str(proofpath)]=sha(proofpath)
 if set(old)!=set(ma):raise ValueError('timing coverage')
 result={}
 for cid in ma:
  c=old[cid]
  if ma[cid][:2]!=mb[cid][:2] or ma[cid]!=(c['net'],c['local_sink_pin'],c['source_rr'],c['target_rr']):raise ValueError('native pin identity changed')
  result[cid]=MappingProxyType(dict(c,source_rr=mb[cid][2],target_rr=mb[cid][3]))
 if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('input changed during remap')
 epoch=sha(Path(criticality_directory)/'initial_connection_criticalities.json')
 return MappingProxyType(result),bindings,epoch
