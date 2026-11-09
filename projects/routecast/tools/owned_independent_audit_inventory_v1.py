"""Parent-owned immutable independent XML inventory with per-use byte checks."""
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read as build
_inventory=None
_key=None
builds=0
hits=0
def read(path,expected):
 global _inventory,_key,builds,hits
 key=(str(Path(path).resolve()),expected)
 if sha(path)!=expected:raise ValueError('graph binding changed')
 if _inventory is None:_inventory=build(path,expected);_key=key;builds+=1
 elif key!=_key:raise ValueError('foreign graph epoch')
 else:hits+=1
 return _inventory
def validate():
 if _key is None or sha(_key[0])!=_key[1]:raise ValueError('graph changed during audit')
def clear():
 global _inventory,_key
 _inventory=None;_key=None
