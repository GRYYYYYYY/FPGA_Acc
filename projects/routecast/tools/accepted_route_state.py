"""Synchronous single-owner quality-selected state advancement.

No concurrent readers, disk publication or crash recovery. Prepared results are
invalidated by revision/content changes. Canonical packed NET hashes may differ
from pre-route NET hashes; placement sites and physical endpoint paths must agree.
"""
import hashlib,json,re
from pathlib import Path
from pre_route_endpoints import sha,placements
from native_route_ledger_import import import_native_ledger

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def state_digest(state):
 return digest({'records':state.records,'ledger':dict(state.ledger),'unions':{n:sorted(v) for n,v in state.unions.items()},'parents':state.parents})

class AcceptedRouteState:
 def __init__(self,state):
  self.ctx=state.ctx;self.state=state;self.revision=0
 def token(self):
  return (self.revision,digest(self.ctx.endpoint_metadata),state_digest(self.state),digest(self.ctx.history))
 def prepare(self,endpoint_path,selection_path,verification_path,expected):
  if expected!=self.token():raise ValueError('stale accepted-state token')
  ep=Path(endpoint_path);sp=Path(selection_path);vp=Path(verification_path)
  q=json.loads(sp.read_text());v=json.loads(vp.read_text());protocol=sp.with_name('protocol.json')
  inputs={str(p):sha(p) for p in (ep,sp,vp,protocol)}
  if v['selection_sha256']!=inputs[str(sp)] or q['protocol_sha256']!=inputs[str(protocol)] or not v['FULL_reload_success'] or q['exit_code']!=0:raise ValueError('unverified quality selection')
  if q['selected'] not in ('reference','predicted') or q['selected_cpd_ns']!=q[q['selected']+'_cpd_ns']:raise ValueError('invalid selection identity')
  if q['selected']!=('predicted' if q['predicted_cpd_ns']<=q['reference_cpd_ns'] else 'reference'):raise ValueError('selection violates quality policy')
  for name,h in q['files_sha256'].items():
   if sha(name)!=h:raise ValueError('selected evidence changed')
   inputs[name]=h
  routes=[Path(name) for name in q['files_sha256'] if Path(name).name=='design.route']
  if len(routes)!=1:raise ValueError('ambiguous selected route')
  route=routes[0];bundle=route.parent;net=bundle/'design.net';place=bundle/'design.place';log=(bundle/'reload.log').read_text()
  for text in ('RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded'):
   if text not in log:raise ValueError('missing native acceptance')
  if float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1])!=q['selected_cpd_ns']:raise ValueError('native timing mismatch')
  for pattern in (r'Found (\d+) mismatches',r'Fixed (\d+) routing traces'):
   match=re.search(pattern,log)
   if not match or int(match[1]):raise ValueError('noncanonical selected route')
  endpoint=json.loads(ep.read_text());cmd=q['command'];graph=cmd[cmd.index('--read_rr_graph')+1]
  if sha(graph)!=endpoint['graph_sha256']:raise ValueError('selection graph mismatch')
  a=placements(place,sha(net));b=placements(Path(endpoint['inputs']['place']['path']),endpoint['inputs']['net']['sha256'])
  if {name:row[:4] for name,row in a.items()}!={name:row[:4] for name,row in b.items()}:raise ValueError('selected placement mismatch')
  original=self.ctx.context;metadata=self.ctx.endpoint_metadata
  try:
   self.ctx.bind_endpoints(ep);state=import_native_ledger(self.ctx,route)
   context=self.ctx.context;new_metadata=self.ctx.endpoint_metadata
  finally:
   self.ctx.context=original;self.ctx.endpoint_metadata=metadata
  prepared={'expected':expected,'state':state,'context':context,'metadata':new_metadata,'inputs':inputs}
  prepared['digest']=self._prepared_digest(prepared)
  return prepared
 def _prepared_digest(self,p):
  return digest([state_digest(p['state']),p['metadata'],p['context'][5],p['inputs']])
 def advance(self,p):
  if p['expected']!=self.token():raise ValueError('stale prepared result')
  if p['state'].ctx is not self.ctx or p['digest']!=self._prepared_digest(p):raise ValueError('prepared state changed')
  if any(sha(path)!=h for path,h in p['inputs'].items()):raise ValueError('prepared evidence changed')
  old=(self.ctx.context,self.ctx.endpoint_metadata,self.state,self.revision,dict(self.ctx.history),{n:self.ctx.native.other[n] for n in self.ctx.native.previous})
  try:
   self.ctx.set_history({});self.ctx.native.set_other({})
   self.ctx.context=p['context'];self.ctx.endpoint_metadata=p['metadata'];self.state=p['state'];self.revision+=1
  except BaseException:
   self.ctx.context,self.ctx.endpoint_metadata,self.state,self.revision=old[:4]
   self.ctx.set_history(old[4]);self.ctx.native.set_other(old[5]);raise
  return self.token()
