"""Isolated JSON model CAS with opaque, generation-bound prepared tickets.

The caller's pure transition must validate physical paths, ledgers and objective.
This layer enforces snapshot/epoch/query identity and all-or-none publication.
It is serial; no process-shared or concurrent-thread synchronization is claimed.
"""
import json,hashlib

def encode(frame):
 return json.dumps(frame,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

class State:
 def __init__(self,frame):
  self._bytes=encode(frame);self._generation=0;self._pending={}
 @property
 def digest(self):return hashlib.sha256(self._bytes).hexdigest()
 def snapshot(self):return json.loads(self._bytes)
 def prepare(self,expected_digest,expected_epochs,transition):
  if expected_digest!=self.digest:raise ValueError('stale source digest')
  before=self.snapshot()
  if any(str(n) not in before['epochs'] or type(e) is not int or e<0 or before['epochs'][str(n)]!=e for n,e in expected_epochs.items()):raise ValueError('stale NET epoch')
  candidate,receipt=transition(self.snapshot())
  old={r['connection_id']:r for r in before['records']};new={r['connection_id']:r for r in candidate['records']}
  if len(old)!=len(before['records']) or len(new)!=len(candidate['records']) or old.keys()!=new.keys():raise ValueError('query set')
  changed=set()
  for cid,r in new.items():
   if {k:v for k,v in r.items() if k!='answer'}!={k:v for k,v in old[cid].items() if k!='answer'}:raise ValueError('frozen query metadata')
   if r['answer']!=old[cid]['answer']:changed.add(str(r['net_id']))
  if not changed:raise ValueError('empty batch')
  if not changed<=set(map(str,expected_epochs)):raise ValueError('missing expected epoch')
  epochs=dict(before['epochs'])
  for net in changed:
   if type(epochs[net]) is not int or epochs[net]<0:raise ValueError('invalid epoch')
   epochs[net]+=1
  if candidate['epochs']!=epochs:raise ValueError('epoch transition')
  payload=encode(candidate);metadata=json.loads(json.dumps(receipt,allow_nan=False))
  token=object();self._pending[token]=(self._generation,self.digest,payload,metadata)
  return token
 def commit(self,token):
  if token not in self._pending:raise ValueError('foreign or consumed ticket')
  generation,digest,payload,receipt=self._pending[token]
  if generation!=self._generation or digest!=self.digest:raise ValueError('stale prepared ticket')
  del self._pending[token]
  self._bytes=payload;self._generation+=1
  return dict(receipt,model_digest=self.digest,generation=self._generation)
