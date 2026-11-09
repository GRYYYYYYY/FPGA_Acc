"""Bounded source-group cache for immutable, frozen-cost regional search.

Key includes the complete requested sink set: changing another sink changes the
region and can change a previously requested sink's physical path. Cache lifetime
is bound to one graph/search instance. No occupancy or epoch state is cached.
"""
from collections import OrderedDict
from copy import deepcopy
from semantic_sketch import SearchResult
from lazy_region_search import LazyRegionalSearch


class CachedRegionalSearch(LazyRegionalSearch):
    def __init__(self,graph,margin=1,max_groups=128):
        if type(max_groups) is not int or max_groups<1:raise ValueError('invalid cache capacity')
        super().__init__(graph,margin);self.max_groups=max_groups;self.cache=OrderedDict()
        self.hits=0;self.misses=0

    def search(self,source,sinks):
        key=(source,frozenset(sinks))
        if key in self.cache:
            self.hits+=1;self.cache.move_to_end(key)
            result,details=self.cache[key]
            details=deepcopy(details)
            details.update(region_node_tests=0,adjacency_filter_probes=0,expanded_adjacency_rows=0,cache_hit=True)
            return SearchResult(deepcopy(result.paths),0,0,result.budget_exhausted),details
        self.misses+=1;result,details=super().search(source,key[1]);details['cache_hit']=False
        self.cache[key]=(deepcopy(result),deepcopy(details))
        if len(self.cache)>self.max_groups:self.cache.popitem(last=False)
        return result,details
