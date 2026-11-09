"""Local hash-bound reuse of audited native bundle evidence; no publication."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
FILES=('design.blif','design.net','design.place','design.route')
def issue(parent,destination):
 parent=Path(parent);dest=Path(destination);receipt=parent/'receipt.json';verification=parent/'verification.json';r=json.loads(receipt.read_text());v=json.loads(verification.read_text())
 if v.get('receipt_sha256')!=sha(receipt) or v.get('verified_bundles')!=1:raise ValueError('canonical verification missing')
 if len(r['results'])!=1:raise ValueError('ambiguous bundle')
 row=r['results'][0];source=Path(row['cwd'])/'reload'
 if row['status']!='RELOADED' or row['sync_mismatches'] or row['sync_fixups']:raise ValueError('noncanonical bundle')
 cmd=row['reload_command'];graph=Path(cmd[cmd.index('--read_rr_graph')+1]);binary=Path(cmd[0]);arch=Path(cmd[1]);log=source/'reload.log'
 # Existing row evidence must itself remain unchanged before any certificate is issued.
 for name,h in row.get('sha256',{}).items():
  if sha(name)!=h:raise ValueError('source evidence changed')
 if sha(graph)!=r['graph_sha256']:raise ValueError('graph changed')
 text=log.read_text()
 for token in ['RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded']:
  if token not in text:raise ValueError('missing FULL proof')
 for pattern in [r'Found (\d+) mismatches',r'Fixed (\d+) routing traces']:
  m=re.search(pattern,text)
  if not m or int(m[1]):raise ValueError('noncanonical proof')
 cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1])
 if cpd!=row['cpd_ns']:raise ValueError('timing changed')
 hashes={n:sha(source/n) for n in FILES}
 if any(sha(dest/n)!=h for n,h in hashes.items()):raise ValueError('copy differs')
 return {'schema':'ROUTECAST_LOCAL_BUNDLE_CERT_V1','bundle_hashes':hashes,'external_hashes':{str(f):sha(f) for f in [receipt,verification,graph,binary,arch,log]},'cpd_ns':cpd,'command':cmd,'scope':'Reuses archived independently audited FULL/STA evidence for identical file bytes and same executable/arch/RR. No fresh execution, signed trust, concurrency or crash recovery.'}
def validate(cert,bundle):
 if cert['schema']!='ROUTECAST_LOCAL_BUNDLE_CERT_V1' or set(cert['bundle_hashes'])!=set(FILES):raise ValueError('invalid schema')
 for n,h in cert['bundle_hashes'].items():
  if sha(Path(bundle)/n)!=h:raise ValueError('bundle changed')
 for name,h in cert['external_hashes'].items():
  if sha(name)!=h:raise ValueError('external evidence changed')
 return cert['cpd_ns']
