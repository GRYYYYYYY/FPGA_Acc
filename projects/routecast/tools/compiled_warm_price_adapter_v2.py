"""Versioned exact uint64-to-wide snapshot bridge for existing warm search."""
from sparse_structural_objective_search_v1 import Search as OriginalSearch
from compiled_criticality_tree_v1 import Graph, NativePrices, BINARY, Words


class Search(OriginalSearch):
    def prepare(self, *args, **kwargs):
        result=super().prepare(*args, **kwargs)
        self.warm_price_version=getattr(self,'warm_price_version',0)+1
        return result

    def patch_prices(self, *args, **kwargs):
        result=super().patch_prices(*args, **kwargs)
        self.warm_price_version=getattr(self,'warm_price_version',0)+1
        return result


_original_buffers=NativePrices.buffers


def buffers(self, graph):
    base, prices, ceiling=_original_buffers(self, graph)
    if hasattr(prices,'buffer'):
        return base, prices, ceiling
    search=self.snapshot.context.search
    key=(self.snapshot.ticket, search.warm_price_version, id(prices),len(prices))
    if getattr(self,'_warm_key',None)!=key:
        self._warm_words=Words(prices)
        self._warm_key=key
    return base,self._warm_words,ceiling


NativePrices.buffers=buffers
