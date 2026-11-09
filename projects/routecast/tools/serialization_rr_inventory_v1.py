"""Owned immutable full node-site/edge inventory for serial route serialization."""
from pathlib import Path
from types import MappingProxyType
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
class SerializationInventory:
 def __init__(self,graph,digest):
  self.graph=Path(graph).resolve();self.digest=digest
  self.validate(graph,digest)
  xml=ET.parse(graph).getroot()
  if xml.tag!='rr_graph':raise ValueError('Expected RR graph')
  nodes={}
  for e in xml.find('rr_nodes'):
   n=int(e.get('id'))
   if n in nodes or e.find('loc') is None:raise ValueError('Invalid node site')
   nodes[n]=(e.get('type'),MappingProxyType(dict(e.find('loc').attrib)))
  self.nodes=MappingProxyType(nodes);self.edges=tuple(tuple(int(e.get(k)) for k in ('src_node','sink_node','switch_id')) for e in xml.find('rr_edges'))
  self.validate(graph,digest)
 def validate(self,graph,digest):
  if Path(graph).resolve()!=self.graph or digest!=self.digest or sha(graph)!=digest:raise ValueError('Serialization inventory epoch changed')
