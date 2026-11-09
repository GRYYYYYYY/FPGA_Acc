"""Independent read-only channel geometry with fresh graph checks on reuse."""
from pathlib import Path
from types import MappingProxyType
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
_key=None
_length=None
builds=0
hits=0
def read(path,expected):
 global _key,_length,builds,hits
 key=(str(Path(path).resolve()),expected)
 if sha(path)!=expected:raise ValueError('graph binding changed')
 if _length is None:
  length={};seen=set()
  for node in ET.parse(path).getroot().find('rr_nodes'):
   n=int(node.get('id'))
   if n in seen:raise ValueError('duplicate node')
   seen.add(n)
   if node.get('type') in ('CHANX','CHANY'):
    loc=node.find('loc');value=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
    if value<1:raise ValueError('invalid channel length')
    length[n]=value
  if sha(path)!=expected:raise ValueError('graph changed during parse')
  _length=MappingProxyType(length);_key=key;builds+=1
 elif key!=_key:raise ValueError('foreign graph epoch')
 else:hits+=1
 return _length
def validate():
 if _key is None or sha(_key[0])!=_key[1]:raise ValueError('graph changed during proof')
def clear():
 global _key,_length
 _key=None;_length=None
