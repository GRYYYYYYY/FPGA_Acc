"""Content-bound native pin identity cache; no route or timing labels stored.

Conservative full-command and net/place/BLIF/architecture/RR/binary bindings.
Caller owns native tool validity. Cache hits authenticate table content; misses
run the identity-only missing-route probe and preserve its log and exit status.
"""
import json,subprocess,os,shutil
from pathlib import Path
from pre_route_endpoints import sha
from accepted_route_state import digest

class NativeIdentityCache:
 def __init__(self,directory):
  self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
 def _bindings(self,command,cwd):
  cmd=list(command);cwd=Path(cwd)
  if '--analysis' not in cmd or '--route_file' not in cmd:raise ValueError('analysis identity probe required')
  inputs={'binary':Path(cmd[0]),'architecture':Path(cmd[1]),'blif':cwd/cmd[2]}
  for name,flag in [('net','--net_file'),('place','--place_file'),('graph','--read_rr_graph')]:
   if flag not in cmd:raise ValueError('explicit identity input required')
   inputs[name]=cwd/cmd[cmd.index(flag)+1]
  probe=cmd.copy();probe[probe.index('--route_file')+1]='routecast_identity_missing.route'
  for index in (0,1,probe.index('--read_rr_graph')+1):probe[index]=str((cwd/probe[index]).resolve())
  if (cwd/'routecast_identity_missing.route').exists():raise ValueError('probe route must be absent')
  return {'command':probe,'inputs_sha256':{name:sha(path) for name,path in inputs.items()}},probe
 def _validate_table(self,path):
  rows=[json.loads(line) for line in Path(path).read_text().splitlines()]
  if not rows or len({r['name'] for r in rows})!=len(rows) or len({r['net_id'] for r in rows})!=len(rows):raise ValueError('invalid identity NET table')
  for row in rows:
   if not isinstance(row['pins'],list) or len({p['index'] for p in row['pins']})!=len(row['pins']):raise ValueError('invalid native pin identity')
  return rows
 def get(self,command,cwd):
  bindings,probe=self._bindings(command,cwd);key=digest(bindings);entry=self.directory/key;manifest=entry/'receipt.json'
  if manifest.exists():
   r=json.loads(manifest.read_text());table=entry/'identity.jsonl'
   if r['bindings']!=bindings or sha(table)!=r['table_sha256'] or sha(entry/'identity.log')!=r['log_sha256']:raise ValueError('identity cache authentication failed')
   rows=self._validate_table(table)
   if self._bindings(command,cwd)[0]!=bindings:raise ValueError('identity inputs changed during cache read')
   return table,{'hit':True,'key':key,'net_count':len(rows),'receipt_sha256':sha(manifest)}
  if entry.exists():raise ValueError('incomplete cache entry; retained for diagnosis')
  entry.mkdir();table=entry/'identity.jsonl';private=entry/'probe';private.mkdir();isolated=probe.copy()
  # VPR may rewrite place formatting: never run against caller input files.
  for name,index in [('blif',2),('net',probe.index('--net_file')+1),('place',probe.index('--place_file')+1)]:
   source=Path(cwd)/probe[index];dest=private/('input_'+name+source.suffix);shutil.copyfile(source,dest);isolated[index]=str(dest.resolve())
  # Absolute read-only architecture, graph and binary references remain valid.
  for index in (0,1,probe.index('--read_rr_graph')+1):isolated[index]=str((Path(cwd)/probe[index]).resolve())
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NET_IDENTITY_FILE']=str(table.resolve())
  with (entry/'identity.log').open('w') as stream:code=subprocess.run(isolated,cwd=private,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
  if code!=1 or not table.exists():raise ValueError('native identity probe failed')
  rows=self._validate_table(table)
  if self._bindings(command,cwd)[0]!=bindings:raise ValueError('identity inputs changed during native probe')
  r={'bindings':bindings,'exit_code':code,'table_sha256':sha(table),'log_sha256':sha(entry/'identity.log'),'net_count':len(rows),'source_sha256':sha(Path(__file__))};manifest.write_text(json.dumps(r,indent=2)+'\n')
  return table,{'hit':False,'key':key,'net_count':len(rows),'receipt_sha256':sha(manifest)}
