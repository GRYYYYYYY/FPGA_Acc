"""Isolated in-memory place/route ledger staging; native validation supplied by caller."""
from copy import deepcopy
from threading import RLock
from transaction_shared_tree_ledger_v1 import TransactionLedger
class StaleEpoch(RuntimeError):pass
class PlaceRouteStore:
 def __init__(self,ledger):
  self._lock=RLock();self._ledger=deepcopy(ledger);self._epoch=0
 def snapshot(self):
  with self._lock:return self._epoch,deepcopy(self._ledger)
 def stage(self,target_queries,replacements,checkpoint=lambda label:None):
  epoch,candidate=self.snapshot();checkpoint('snapshot')
  if set(target_queries)!=set(candidate.queries):raise ValueError('demand identity changed')
  replacements={cid:tuple(tuple(x) for x in path) for cid,path in replacements.items()}
  for cid in sorted(replacements):candidate.release(cid);checkpoint('release:'+str(cid))
  candidate.queries=deepcopy(target_queries);checkpoint('query_epoch')
  for cid in sorted(replacements):candidate.insert(cid,replacements[cid]);checkpoint('insert:'+str(cid))
  if set(candidate.state)!=set(target_queries):raise ValueError('incomplete staged state')
  for cid,path in candidate.state.items():candidate._validate_endpoints(cid,path)
  checkpoint('ready');return epoch,candidate
 def commit(self,staged,validate,checkpoint=lambda label:None):
  epoch,candidate=staged
  # Validate an isolated copy; callback cannot modify the publish candidate.
  validate(deepcopy(candidate));checkpoint('validated')
  with self._lock:
   if epoch!=self._epoch:raise StaleEpoch('committed epoch changed')
   published=deepcopy(candidate);checkpoint('before_publish')
   self._ledger=published;self._epoch+=1
  return self._epoch
