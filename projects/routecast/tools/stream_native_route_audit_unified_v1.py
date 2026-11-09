"""Stream RR XML to audit every printed native branch, retaining used arcs only.

Full required arc/switch identity, rooted branch structure, terminal occurrences
and unique-net accounting; not equivalent-site pin legality or closure proof.
"""
from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
from native_route_audit_cache import snapshot

def audit(graph_path,route_path,inventory):
 before={'graph':sha(graph_path),'route':sha(route_path)};nets={};types={};needed=set();connections=[];net=None;parents={};depth={};current=None;outgoing=None;source=None;printed=0
 for line in Path(route_path).read_text().splitlines():
  m=NET.match(line)
  if m:
   net=int(m[1])
   if net in nets:raise ValueError('duplicate net')
   nets[net]=set();parents={};depth={};current=None;source=None;outgoing=None
  m=NODE.match(line)
  if not m:
   if line.lstrip().startswith('Node:'):raise ValueError('unparsed node')
   continue
  if net is None:raise ValueError('node before net')
  nid=int(m[1]);kind=m[2];switch=int(m[3]);printed+=1
  if nid in types and types[nid]!=kind:raise ValueError('inconsistent node type')
  types[nid]=kind;nets[net].add(nid)
  if nid in parents and kind!='SINK':pass
  elif kind=='SOURCE':
   if parents:raise ValueError('multiple source roots')
   source=nid;parents[nid]=None;depth[nid]=0
  else:
   if current is None or types[current]=='SINK':raise ValueError('branch without nonterminal predecessor')
   needed.add((current,nid,outgoing))
   if kind=='SINK':connections.append({'net_id':net,'source':source,'sink':nid,'hops':depth[current]+1})
   else:parents[nid]=current;depth[nid]=depth[current]+1
  current=nid;outgoing=switch
 if inventory.digest!=before['graph']:raise ValueError('Wrong inventory epoch')
 frozen=inventory.physical;physical={};found={};switches=frozen.switches;edge_count=frozen.edge_count
 for nid,kind in types.items():
  if nid not in frozen.nodes:continue
  actual,capacity=frozen.nodes[nid]
  if nid in frozen.duplicate_nodes or actual!=kind:raise ValueError('physical node mismatch')
  physical[nid]=int(capacity)
 for key in needed:
  if key in frozen.arcs:found[key]=frozen.arcs[key]
 if set(physical)!=set(types):raise ValueError('printed node absent from RR graph')
 if set(found)!=needed or any(s not in switches for u,v,s in needed):raise ValueError('printed arc/switch absent from RR graph')
 demand=Counter(n for used in nets.values() for n in used)
 if any(physical[n]<=0 for n in demand):raise ValueError('printed disabled node')
 if before!={'graph':sha(graph_path),'route':sha(route_path)}:raise ValueError('input changed')
 return {'inputs_sha256':before,'connections':connections,'node_occupancy':{str(n):v for n,v in demand.items()},'routed_nets':sum(bool(v) for v in nets.values()),'printed_nodes':printed,'required_distinct_arcs':len(needed),'physical_edge_count':edge_count,'occupied_nodes':len(demand),'overflow_units':sum(max(0,v-physical[n]) for n,v in demand.items()),'all_printed_branch_arc_switch_and_union_checks_pass':True,'scope':'native printed physical branches and unique-net capacity accounting, not full pin/nonconfigurable legality or new routing QoR'}
