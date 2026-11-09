"""Exact wide-buffer refresh and stale-snapshot guard tests."""
from array import array
from types import SimpleNamespace as N
from compiled_warm_price_adapter_v2 import NativePrices,Search
from cached_multiplicative_occupancy_context_v1 import PriceView
from sparse_structural_objective_search_v1 import Search as Parent

def main():
 base=(3,5,7);prices=array('Q',[0,2**64-1,42]);search=N(closed=False,prepared=True,structural=True,weight=1,backends=[None,N(forward=N(price=prices))],price_ceiling=2**64,warm_price_version=1);context=N(base=base,search=search,active=9);view=PriceView(context,9);native=NativePrices(base,view);graph=N(n=3,base_owner=None);b,p,c=native.buffers(graph);assert p[:]==list(prices);assert native.buffers(graph)[1] is p;checks=2
 prices[2]=123;search.warm_price_version+=1;new=native.buffers(graph)[1];assert new is not p and new[:]==list(prices);checks+=1
 context.active=None
 try:native.buffers(graph)
 except RuntimeError:checks+=1
 else:raise AssertionError('stale snapshot')
 context.active=9;search.closed=True
 try:native.buffers(graph)
 except RuntimeError:checks+=1
 else:raise AssertionError('closed search')
 # Independently confirm both prepare and patch methods advance the version.
 original_prepare,original_patch=Parent.prepare,Parent.patch_prices
 try:
  Parent.prepare=lambda self,*a,**k:None;Parent.patch_prices=lambda self,*a,**k:None
  obj=Search.__new__(Search);obj.prepare();assert obj.warm_price_version==1;obj.patch_prices({});assert obj.warm_price_version==2;checks+=2
 finally:Parent.prepare,Parent.patch_prices=original_prepare,original_patch
 print('ALL7_WIDE_PRICE_BUFFER_AND_VERSION_GUARDS_PASS',checks)
if __name__=='__main__':main()
