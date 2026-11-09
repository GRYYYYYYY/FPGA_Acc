"""Versioned exact uint64-to-wide snapshot bridge for existing warm search."""
from array import array
import ctypes
from wide_cost_search_bridge_v2 import Word
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


class PackedWords:
    def __init__(self, values):
        if type(values) is not array or values.typecode != 'Q' or values.itemsize != 8:
            raise ValueError('requires native unsigned64 array')
        assert ctypes.sizeof(Word) == 16 and Word.lo.offset == 0 and Word.hi.offset == 8
        self.owner = array('Q', [0]) * (2 * len(values))
        self.owner[::2] = values
        self.buffer = (Word * len(values)).from_buffer(self.owner)
    def __len__(self):return len(self.buffer)
    def __getitem__(self, index):
        if isinstance(index, slice):return [v.integer() for v in self.buffer[index]]
        return self.buffer[index].integer()


_original_buffers=NativePrices.buffers


def buffers(self, graph):
    base, prices, ceiling=_original_buffers(self, graph)
    if hasattr(prices,'buffer'):
        return base, prices, ceiling
    search=self.snapshot.context.search
    key=(self.snapshot.ticket, search.warm_price_version, id(prices),len(prices))
    if getattr(self,'_warm_key',None)!=key:
        self._warm_words=PackedWords(prices) if type(prices) is array and prices.typecode=='Q' and prices.itemsize==8 else Words(prices)
        self._warm_key=key
    return base,self._warm_words,ceiling


NativePrices.buffers=buffers
