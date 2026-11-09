"""Isolated synchronous owner accepting caller hash-bound local certificates."""
import json
from pathlib import Path
from accepted_route_state import AcceptedRouteState,digest
from validated_bundle_certificate import validate,FILES
from pre_route_endpoints import sha,placements
from native_route_ledger_import import import_native_ledger
class CertifiedAcceptedRouteState(AcceptedRouteState):
 def prepare_certified(self,endpoint_path,alternatives,expected):
  if expected!=self.token():raise ValueError('stale accepted-state token')
  if set(alternatives)!= {'reference','predicted'}:raise ValueError('two alternatives required')
  ep=Path(endpoint_path);endpoint=json.loads(ep.read_text());inputs={str(ep):sha(ep)};cases={}
  for label,entry in alternatives.items():
   cp=Path(entry['certificate']);bundle=Path(entry['bundle'])
   if sha(cp)!=entry['certificate_sha256']:raise ValueError('certificate bytes changed')
   c=json.loads(cp.read_text());cpd=validate(c,bundle);inputs[str(cp)]=entry['certificate_sha256'];inputs.update(c['external_hashes'])
   inputs.update({str(bundle/n):h for n,h in c['bundle_hashes'].items()})
   graph=c['command'][c['command'].index('--read_rr_graph')+1]
   if sha(graph)!=endpoint['graph_sha256']:raise ValueError('graph mismatch')
   sites=placements(bundle/'design.place',sha(bundle/'design.net'));target=placements(Path(endpoint['inputs']['place']['path']),endpoint['inputs']['net']['sha256'])
   if {k:v[:4] for k,v in sites.items()}!={k:v[:4] for k,v in target.items()}:raise ValueError('placement mismatch')
   cases[label]=(c,bundle,cpd)
  if cases['reference'][0]['bundle_hashes']['design.blif']!=cases['predicted'][0]['bundle_hashes']['design.blif']:raise ValueError('BLIF mismatch')
  selected='predicted' if cases['predicted'][2]<=cases['reference'][2] else 'reference';c,bundle,cpd=cases[selected]
  original=self.ctx.context;metadata=self.ctx.endpoint_metadata
  try:
   self.ctx.bind_endpoints(ep);state=import_native_ledger(self.ctx,bundle/'design.route');context=self.ctx.context;new_metadata=self.ctx.endpoint_metadata
  finally:self.ctx.context=original;self.ctx.endpoint_metadata=metadata
  p={'expected':expected,'state':state,'context':context,'metadata':new_metadata,'inputs':inputs,'selection':{'selected':selected,'selected_cpd_ns':cpd,'reference_cpd_ns':cases['reference'][2],'predicted_cpd_ns':cases['predicted'][2],'evidence_mode':'REUSED_ARCHIVED_FULL_STA'}};p['digest']=self._prepared_digest(p);return p
 def _prepared_digest(self,p):return digest([super()._prepared_digest(p),p.get('selection')])
