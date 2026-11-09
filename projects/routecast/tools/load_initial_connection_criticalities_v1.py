"""Load authenticated initial native timing proxy without consuming final route labels."""
import json,struct,math
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha

def load(directory):
 directory=Path(directory)
 proof=directory/'verification.json'
 admission=json.loads(proof.read_text())
 if not admission.get('nonignored_pin_keys_exactly_manifest') or not admission.get('all_values_and_pin_identities_equal_v1'):
  raise ValueError('initial criticality admission missing')
 if not all(sha(p)==h for p,h in admission['bindings'].items()):
  raise ValueError('initial criticality source binding changed')
 path=directory/'initial_connection_criticalities.json'
 if str(path.resolve()) not in admission['bindings']:
  raise ValueError('criticality vector not bound')
 rows=json.loads(path.read_text());by_id={};keys=set()
 for row in rows:
  cid=row['connection_id'];key=row['net'],row['local_sink_pin']
  if type(cid) is not int or cid<0 or cid in by_id or key in keys:raise ValueError('duplicate/invalid connection identity')
  value=struct.unpack('f',struct.pack('f',float(row['criticality_float32_text'])))[0]
  maximum=struct.unpack('f',struct.pack('f',float(row['maximum_text'])))[0]
  if not math.isfinite(value) or not 0<=value<=maximum<=1:raise ValueError('invalid criticality')
  numerator,denominator=value.as_integer_ratio()
  by_id[cid]=MappingProxyType(dict(row,criticality=value,criticality_numerator=numerator,criticality_denominator=denominator))
  keys.add(key)
 if len(by_id)!=admission['routed_connections']:raise ValueError('incomplete criticality vector')
 return MappingProxyType(by_id)

if __name__=='__main__':
 import sys
 vector=load(sys.argv[1]);assert len(vector)==115572
 print('INITIAL CRITICALITY LOAD PASS',len(vector),'exact float32 range',min(x['criticality'] for x in vector.values()),max(x['criticality'] for x in vector.values()))
