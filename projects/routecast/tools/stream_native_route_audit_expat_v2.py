"""Experimental complete Expat callback scan; original route checks unchanged."""
"""Stream RR XML to audit every printed native branch, retaining used arcs only.

Full required arc/switch identity, rooted branch structure, terminal occurrences
and unique-net accounting; not equivalent-site pin legality or closure proof.
"""
from pathlib import Path
from collections import Counter
from xml.parsers import expat
from audit_native_route import NET,NODE
from pre_route_endpoints import sha

def audit(graph_path,route_path):
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
 found={};physical={};switches=set();edge_count=0;stack=[]
 def expanded(name):
  return "{"+name.replace("\x1f", "}", 1) if "\x1f" in name else name
 def start(raw_tag,raw_attrs):
  tag=expanded(raw_tag);attrs={expanded(k):v for k,v in raw_attrs.items()}
  nonlocal edge_count
  parent=stack[-1] if stack else None
  if tag=='switch' and parent=='switches':switches.add(int(attrs['id']))
  if tag=='node' and parent=='rr_nodes':
   nid=int(attrs['id'])
   if nid in types:
    if nid in physical or attrs['type']!=types[nid]:raise ValueError('physical node mismatch')
    physical[nid]=int(attrs['capacity'])
  if tag=='edge' and parent=='rr_edges':
   key=(int(attrs['src_node']),int(attrs['sink_node']),int(attrs['switch_id']))
   if key in needed and key not in found:found[key]=edge_count
   edge_count+=1
  stack.append(tag)
 def end(tag):
  assert stack.pop()==expanded(tag)
 parser=expat.ParserCreate(namespace_separator="\x1f")
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with Path(graph_path).open('rb') as stream:parser.ParseFile(stream)
 if set(physical)!=set(types):raise ValueError('printed node absent from RR graph')
 if set(found)!=needed or any(s not in switches for u,v,s in needed):raise ValueError('printed arc/switch absent from RR graph')
 demand=Counter(n for used in nets.values() for n in used)
 if any(physical[n]<=0 for n in demand):raise ValueError('printed disabled node')
 if before!={'graph':sha(graph_path),'route':sha(route_path)}:raise ValueError('input changed')
 return {'inputs_sha256':before,'connections':connections,'node_occupancy':{str(n):v for n,v in demand.items()},'routed_nets':sum(bool(v) for v in nets.values()),'printed_nodes':printed,'required_distinct_arcs':len(needed),'physical_edge_count':edge_count,'occupied_nodes':len(demand),'overflow_units':sum(max(0,v-physical[n]) for n,v in demand.items()),'all_printed_branch_arc_switch_and_union_checks_pass':True,'scope':'native printed physical branches and unique-net capacity accounting, not full pin/nonconfigurable legality or new routing QoR'}
