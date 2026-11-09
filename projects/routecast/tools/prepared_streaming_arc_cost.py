"""Exact scalar arc costs with prevalidated node RC equivalence class IDs."""
from array import array
from path_rc import number
from streaming_cached_arc_cost import StreamingCachedArcCost
class PreparedStreamingArcCost:
    def __init__(self,switches,bases,normalization,resistance,capacitance,indices,capacities,scale=10**6):
        self.scalar=StreamingCachedArcCost(switches,bases,normalization,scale)
        n=len(resistance)
        if not (len(capacitance)==len(indices)==len(capacities)==n):raise ValueError('node length mismatch')
        self.sources=array('Q');self.destinations=array('Q');self.indices=array('Q');self.capacities=array('Q')
        srank={};drank={};self.source_values=[];self.destination_values=[]
        for r,c,i,cap in zip(resistance,capacitance,indices,capacities):
            r=number(r);c=number(c)
            if type(i) is not int or i not in self.scalar.bases:raise ValueError('invalid cost index')
            if type(cap) is not int or cap<0:raise ValueError('invalid capacity')
            if r not in srank:srank[r]=len(srank);self.source_values.append(r)
            if (r,c) not in drank:drank[r,c]=len(drank);self.destination_values.append((r,c))
            self.sources.append(srank[r]);self.destinations.append(drank[r,c]);self.indices.append(i);self.capacities.append(cap)
        self.cache={};self.queries=0
    def cost(self,switch_id,source_rank,destination_rank):
        n=len(self.sources)
        if type(switch_id) is not int or switch_id not in self.scalar.switches:raise ValueError('invalid switch ID')
        if any(type(r) is not int or not 0<=r<n for r in (source_rank,destination_rank)):raise ValueError('invalid node rank')
        key=(switch_id,self.sources[source_rank],self.destinations[destination_rank],self.indices[destination_rank]);self.queries+=1
        if key not in self.cache:
            r,c=self.destination_values[key[2]]
            # Always compute a live scalar cost first; disabled arcs still validate.
            self.cache[key]=self.scalar.cost(switch_id,self.source_values[key[1]],r,c,key[3],1)
        return self.cache[key] if self.capacities[destination_rank] else None
