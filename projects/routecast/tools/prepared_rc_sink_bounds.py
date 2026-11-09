"""Pinned, independently certified exact RC sink arrays; no unknown sink fallback."""
import json,hashlib,sys
from pathlib import Path
from pre_route_endpoints import sha

class PreparedRCSinkBounds:
 def __init__(self,root,expected_receipt_sha256,graph_sha256,scale,nodes):
  self.root=Path(root);data=(self.root/'receipt.json').read_bytes()
  if hashlib.sha256(data).hexdigest()!=expected_receipt_sha256:raise ValueError('changed pinned sink receipt')
  receipt=json.loads(data)
  if receipt['schema']!='ROUTECAST_EXACT_RC_SINK_BOUNDS_V1' or receipt['graph_sha256']!=graph_sha256 or receipt['scale']!=scale or receipt['nodes']!=nodes or receipt['byteorder']!='little' or sys.byteorder!='little' or receipt['unreachable_sentinel']!=(1<<64)-1:raise ValueError('incompatible bound context')
  if not all(sha(Path(p))==h for p,h in receipt['inputs_sha256'].items()):raise ValueError('changed original bound inputs')
  self.nodes=nodes;self.entries={};self.cache={}
  for row in receipt['sinks']:
   sink=row['sink']
   if type(sink) is not int or not 0<=sink<nodes or sink in self.entries or row['payload']!=f'sink_{sink}.bin':raise ValueError('invalid bound sink identity')
   if row['certificate']['all_distance_and_tight_path_checks_passed'] is not True:raise ValueError('uncertified remaining distances')
   self.entries[sink]=row
 def get(self,sink):
  if type(sink) is not int or sink not in self.entries:raise ValueError('unprepared sink')
  if sink not in self.cache:
   row=self.entries[sink];data=(self.root/row['payload']).read_bytes()
   if len(data)!=8*self.nodes or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('changed bound payload')
   values=memoryview(data).cast('Q')
   if values[sink]!=0:raise ValueError('invalid sink terminal distance')
   self.cache[sink]=values
  return self.cache[sink]
