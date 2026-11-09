"""Authenticate a deliberately rehashed wrong cost, then require XML audit rejection."""
import tempfile,json,hashlib,shutil
from pathlib import Path
from pre_route_endpoints import sha
from audit_stereo_streaming_csr import audit
source=Path('experiments/clma_streaming_independent_audit_2026-10-05')
out=Path('experiments/clma_cost_audit_rejection_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir();shutil.copyfile(__file__,out/'driver.py')
with tempfile.TemporaryDirectory(prefix='routecast_wrong_cost_') as directory:
 root=Path(directory);(root/'csr').mkdir();p=json.loads((source/'protocol.json').read_text());(root/'protocol.json').write_text(json.dumps(p)+'\n');m=json.loads((source/'csr/manifest.json').read_text())
 for spec in m['files'].values():
  a=source/'csr'/spec['file'];b=root/'csr'/spec['file']
  if spec['file']=='costs.bin':
   shutil.copyfile(a,b)
   with b.open('r+b') as stream:
    old=int.from_bytes(stream.read(8),'little');stream.seek(0);stream.write((old+1).to_bytes(8,'little'))
   spec['sha256']=sha(b)
  else:b.symlink_to(a.resolve())
 m['context']['cost_payload_sha256']=m['files']['costs']['sha256'];m['context_sha256']=hashlib.sha256(json.dumps(m['context'],sort_keys=True).encode()).hexdigest()
 (root/'csr/manifest.json').write_text(json.dumps(m,indent=2)+'\n');(root/'receipt.json').write_text(json.dumps({'manifest_sha256':sha(root/'csr/manifest.json'),'protocol_sha256':sha(root/'protocol.json')})+'\n')
 try:audit(root)
 except AssertionError as error:
  assert error.args and isinstance(error.args[0],tuple) and error.args[0][-1]=='cost',error
  result={'authenticated_cost_modified':True,'independent_formula_rejected':True,'error':repr(error),'source_sha256':sha(__file__),'original_inputs_unchanged':True}
 else:raise AssertionError('wrong cost accepted')
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
