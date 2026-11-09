"""Serial query-result cache; caller authenticates complete native read traces.

Context must bind graph, electrical data, eligibility, implementation, endpoints,
NET ownership, RC budget and label limit. It excludes demand, checked on reads.
No external allocation failure, transactional or concurrent publication guarantee.
"""
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Record:
 context:str
 demands:tuple
 result:bytes

class RCReadDependencyCache:
 def __init__(self,nodes):self.nodes=nodes;self.records={}
 def _context(self,context):
  if type(context) is not str or len(context)!=64 or any(c not in '0123456789abcdef' for c in context):raise ValueError('authenticated context digest required')
 def _value(self,other,node):
  value=other.get(node,0)
  if type(value) is not int or not 0<=value<(1<<64):raise ValueError('invalid exact demand')
  return value
 def lookup(self,slot,context,other):
  self._context(context);record=self.records.get(slot)
  if record is None or record.context!=context:return None
  if any(self._value(other,n)!=v for n,v in record.demands):return None
  return json.loads(record.result),frozenset(n for n,v in record.demands)
 def store(self,slot,context,other,footprint,result):
  self._context(context)
  if result['status'] not in ('FOUND','UNREACHABLE','LABEL_LIMIT','ARITHMETIC_LIMIT'):return False
  nodes=frozenset(footprint)
  if any(type(n) is not int or not 0<=n<self.nodes for n in nodes):raise ValueError('invalid trace node')
  demands=tuple((n,self._value(other,n)) for n in sorted(nodes))
  payload=json.dumps(result,allow_nan=False,separators=(',',':')).encode()
  record=Record(context,demands,payload)
  self.records[slot]=record
  return True
 def payload(self):
  return json.dumps([[slot,r.context,list(r.demands),json.loads(r.result)] for slot,r in self.records.items()],allow_nan=False,separators=(',',':')).encode()
 @classmethod
 def restore(cls,nodes,payload):
  if type(payload) is not bytes:raise ValueError('immutable cache payload required')
  cache=cls(nodes)
  if not payload:return cache
  for slot,context,demands,result in json.loads(payload):
   if slot in cache.records:raise ValueError('duplicate cache slot')
   other=dict(demands)
   if len(other)!=len(demands):raise ValueError('duplicate dependency node')
   if not cache.store(slot,context,other,other,result):raise ValueError('unsupported cached status')
  return cache
