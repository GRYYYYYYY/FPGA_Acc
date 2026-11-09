"""Authenticated first-FULL sync capture reuse for canonical reload preparation.

Does not replace packed-pin mapping, original VPR canonical FULL reload or quality
selection. Directory staging is isolated; no live route state is published.
"""
import json,re,shutil,tempfile,os
from dataclasses import dataclass
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit

@dataclass(frozen=True)
class NativeCaptureEvidence:
 bindings: tuple
 sources: tuple
 receipt_sha256: str
 graph_sha256: str
 connections: int
 cpd_ns: float
 def validate(self):
  if any(sha(path)!=h for path,h in self.bindings):raise ValueError('native capture evidence changed')
 def stage(self,destination):
  dest=Path(destination)
  if dest.exists():raise ValueError('fresh capture destination required')
  self.validate();dest.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='.capture-',dir=dest.parent) as temp:
   temp=Path(temp)
   for name,path,h in self.sources:
    shutil.copyfile(path,temp/name)
    if sha(temp/name)!=h:raise ValueError('capture copy mismatch')
   self.validate()
   manifest={'source_sha256':sha(Path(__file__)),'receipt_sha256':self.receipt_sha256,'graph_sha256':self.graph_sha256,'connections':self.connections,'cpd_ns':self.cpd_ns,'source_bindings':dict(self.bindings),'files_sha256':{name:h for name,path,h in self.sources},'scope':'First successful FULL sync evidence staged; canonical FULL reload and quality selection still required.'}
   (temp/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
   os.rename(temp,dest)
  return dest/'manifest.json'

def load_capture_evidence(receipt_path,verification_path,cwd,graph,graph_sha256,connections,log_name='import.log'):
 receipt=Path(receipt_path);verification=Path(verification_path);cwd=Path(cwd);graph=Path(graph)
 inputs={str(p):sha(p) for p in (receipt,verification,graph)};q=json.loads(receipt.read_text());v=json.loads(verification.read_text())
 if v['receipt_sha256']!=inputs[str(receipt)] or q['exit_code']!=0 or not q['native_success']:raise ValueError('unverified native producer')
 if log_name not in ('import.log','run.log'):raise ValueError('unsupported native log binding')
 cmd=q['command'] if 'command' in q else None
 if cmd is None:
  protocol=receipt.with_name('protocol.json');inputs[str(protocol)]=sha(protocol)
  if inputs[str(protocol)]!=q['protocol_sha256']:raise ValueError('native protocol changed')
  cmd=json.loads(protocol.read_text())['command']
 binary=Path(cmd[0]);build=binary.parent/'receipt.json';build_protocol=binary.parent/'protocol.json'
 if binary.name!='routecast_sync_capture_vpr' or binary.parent.name!='native_route_sync_capture_v2_2026-10-06':raise ValueError('sync capture producer required')
 for p in (binary,build,build_protocol,Path(cmd[1])):inputs[str(p)]=sha(p)
 br=json.loads(build.read_text())
 if br['binary_sha256']!=inputs[str(binary)] or br['protocol_sha256']!=inputs[str(build_protocol)]:raise ValueError('capture binary provenance mismatch')
 if inputs[str(graph)]!=graph_sha256 or sha(cmd[cmd.index('--read_rr_graph')+1])!=graph_sha256:raise ValueError('capture graph mismatch')
 if '--check_route' not in cmd or cmd[cmd.index('--check_route')+1]!='full':raise ValueError('FULL route check required')
 for p,h in q['files_sha256'].items():
  if sha(p)!=h:raise ValueError('producer output changed')
  inputs[p]=h
 log=cwd/log_name
 if str(log) not in q['files_sha256']:raise ValueError('native log not bound')
 text=log.read_text()
 for token in ('RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded'):
  if token not in text:raise ValueError('native FULL acceptance missing')
 match=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)
 if not match or float(match[1])!=q['cpd_ns']:raise ValueError('capture timing mismatch')
 sources=[]
 for name in ('before_sync.route','after_sync.route','design.net.post_routing'):
  path=cwd/name
  if str(path) not in q['files_sha256']:raise ValueError('capture artifact not bound')
  sources.append((name,str(path),q['files_sha256'][str(path)]))
 sources.append(('capture.log',str(log),q['files_sha256'][str(log)]))
 a=audit(graph,cwd/'before_sync.route');b=audit(graph,cwd/'after_sync.route')
 if len(a['connections'])!=connections or len(b['connections'])!=connections or a['overflow_units'] or b['overflow_units']:raise ValueError('capture physical closure mismatch')
 before=physical_paths(cwd/'before_sync.route');after=physical_paths(cwd/'after_sync.route')
 if {n:sorted(paths) for n,paths in before.items()}!={n:sorted(paths) for n,paths in after.items()}:raise ValueError('sync changed physical paths')
 result=NativeCaptureEvidence(tuple(sorted(inputs.items())),tuple(sources),inputs[str(receipt)],graph_sha256,connections,q['cpd_ns']);result.validate();return result
