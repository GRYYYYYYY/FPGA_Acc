import sys,json,re,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from stream_native_route_audit import audit
from audit_native_route import NET
root=Path.cwd(); out=root/'experiments/native_identity_remapped_reload_2026-10-06'; source=root/'work/native_synchronized_bundle_reload_2026-10-06/rebound_bundle'
command=json.loads((root/'experiments/native_synchronized_bundle_reload_2026-10-06/rebound_bundle_command.json').read_text())['command']; graph=command[command.index('--read_rr_graph')+1]
def canonical(path):
 sections={}; current=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:
   current=re.sub(r'^Net\s+\d+', 'Net ID',line); assert current not in sections;sections[current]=[]
  elif current is not None:
   sections[current].append(re.sub(r'Net_pin_index:\s*\d+','Net_pin_index: ID',line))
 return sections
assert canonical(source/'design.route')==canonical(out/'remapped.route')
physical=audit(graph,out/'remapped.route'); assert len(physical['connections'])==129 and physical['overflow_units']==0
(out/'physical_audit.json').write_text(json.dumps(physical,indent=2)+'\n')
paths=[Path(graph),Path(command[0]),source/'design.net',source/'design.place',out/'remapped.route',out/'mapping.json',out/'reload.log',root/'tools/trial_native_identity_remapped_reload.py',root/'experiments/native_net_identity_capture_2026-10-06/original.jsonl',root/'experiments/native_net_identity_capture_2026-10-06/synchronized.jsonl']
verification={'physical_geometry_branches_switches_unchanged_by_net_name':True,'connections':129,'overflow_units':0,'inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'Independent XML physical audit and normalized trace comparison; native reload is analysis only, no formal logical equivalence or persistent reroute claim.'}
(out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print('Verified 129 connections, zero overflow, unchanged physical trace by NET name')
