"""Single-owner live perNET union ledger shared across repair stages.

No concurrent readers or exception rollback are provided. Inputs must belong to
the same authenticated context. Serialization is a snapshot, not publication.
"""
from collections import Counter,defaultdict
class RouteLedgerState:
 def __init__(self,ctx):
  self.ctx=ctx
  f=ctx.rc.fields
  self.slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(ctx.native.n) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
  self.unions=defaultdict(set);self.parents=defaultdict(dict)
  self.records={};self.ledger=Counter()
 def check_prior(self,ctx,prior):
  if ctx is not self.ctx:raise ValueError('ledger context mismatch')
  if self.records!={r['connection_id']:r for r in prior['records']} or dict(self.ledger)!={int(n):c for n,c in prior['ledger'].items()}:
   raise ValueError('retained state does not match prior snapshot')
