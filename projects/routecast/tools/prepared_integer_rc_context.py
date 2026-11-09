"""Trusted prepared exact lattice; caller pins receipt digest and original inputs."""
import json,sys,hashlib
from array import array
from pathlib import Path
from integer_rc_context import IntegerRC
from pre_route_endpoints import sha

def prepare(root,rc,bindings):
 root=Path(root);root.mkdir();integer=IntegerRC(rc)
 if sys.byteorder!='little':raise ValueError('little-endian preparation required')
 increments=array('Q',integer.increments);initial=array('Q')
 for n in range(len(rc.fields['node_ids'])):
  value=integer.initial(n)
  if not 0<=value<(1<<128):raise ValueError('uint128 initial required')
  initial.extend((value&((1<<64)-1),value>>64))
 (root/'increments.bin').write_bytes(increments.tobytes());(root/'initial.bin').write_bytes(initial.tobytes())
 for i,v in enumerate(increments):assert integer.encode(rc.increment(i))==v
 for n in range(len(rc.fields['node_ids'])):assert initial[2*n]+(initial[2*n+1]<<64)==integer.initial(n)
 if not all(sha(Path(p))==h for p,h in bindings.items()):raise ValueError('preparation inputs changed')
 receipt={'schema':'ROUTECAST_PREPARED_INTEGER_RC_V1','nodes':len(rc.fields['node_ids']),'edges':len(increments),'scale':integer.scale,'byteorder':'little','inputs_sha256':bindings,'outputs_sha256':{n:sha(root/n) for n in ('increments.bin','initial.bin')},'generator_sha256':sha(Path(__file__))}
 (root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return sha(root/'receipt.json')

class PreparedIntegerRC(IntegerRC):
 def __init__(self,rc,root,expected_receipt_sha256):
  root=Path(root)
  receipt_bytes=(root/'receipt.json').read_bytes()
  if hashlib.sha256(receipt_bytes).hexdigest()!=expected_receipt_sha256:raise ValueError('changed pinned integer receipt')
  receipt=json.loads(receipt_bytes)
  if receipt['schema']!='ROUTECAST_PREPARED_INTEGER_RC_V1' or receipt['byteorder']!='little' or sys.byteorder!='little':raise ValueError('unsupported lattice format')
  if type(receipt['scale']) is not int or receipt['scale']<1 or receipt['nodes']!=len(rc.fields['node_ids']) or receipt['edges']!=len(rc.fields['edge_ids']):raise ValueError('invalid lattice dimensions')
  if not all(sha(Path(p))==h for p,h in receipt['inputs_sha256'].items()):raise ValueError('changed original lattice input')
  increments=(root/'increments.bin').read_bytes();initial=(root/'initial.bin').read_bytes()
  if any(hashlib.sha256(data).hexdigest()!=receipt['outputs_sha256'][n] for n,data in (('increments.bin',increments),('initial.bin',initial))):raise ValueError('changed prepared lattice')
  if len(increments)!=8*receipt['edges'] or len(initial)!=16*receipt['nodes']:raise ValueError('invalid lattice payload size')
  self.rc=rc;self.fields=rc.fields;self.scale=receipt['scale'];self.increments=memoryview(increments).cast('Q');self.initials=memoryview(initial).cast('Q')
 def initial(self,n):
  self.node(n);return self.initials[2*n]+(self.initials[2*n+1]<<64)
