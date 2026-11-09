"""Graph-bound exchange CSR lookup; duplicate arcs keep the final CSR slot.

Shares only structural data. Requires the existing context's graph arrays to
remain unchanged in memory, as the indexed RC evaluator already does.
"""
from types import MappingProxyType
from shared_rr_inventory import SharedRRInventory

def exchange_slot_index(fields,n):
 offsets=fields['row_offsets'];dest=fields['dest_ranks'];switches=fields['switch_ids']
 if len(offsets)!=n+1 or offsets[0]!=0 or offsets[-1]!=len(dest) or len(switches)!=len(dest):raise ValueError('CSR coverage')
 result={}
 for u in range(n):
  if not 0<=offsets[u]<=offsets[u+1]<=len(dest):raise ValueError('CSR offset')
  for slot in range(offsets[u],offsets[u+1]):
   if not 0<=dest[slot]<n:raise ValueError('CSR destination')
   result[u,dest[slot],switches[slot]]=slot
 return MappingProxyType(result)

class SharedRRInventorySlots(SharedRRInventory):
 def __init__(self,ctx):
  super().__init__(ctx)
  self._exchange_fields=ctx.fields;self._exchange_n=ctx.n
  self._exchange_slots=exchange_slot_index(ctx.fields,ctx.n)
  self._exchange_spans=tuple(1+int(loc['xhigh'])-int(loc['xlow'])+int(loc['yhigh'])-int(loc['ylow']) if kind in ('CHANX','CHANY') else 0 for kind,loc in (self.nodes[n] for n in range(ctx.n)))
 def exchange_structure(self,ctx):
  if ctx.fields is not self._exchange_fields or ctx.n!=self._exchange_n or str(ctx.graph)!=str(self.graph) or ctx.digest!=self.digest:raise ValueError('exchange context mismatch')
  return self._exchange_slots,self._exchange_spans
