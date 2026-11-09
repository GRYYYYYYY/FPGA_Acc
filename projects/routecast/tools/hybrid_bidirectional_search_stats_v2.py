"""Diagnostic hybrid branch counters; timing includes instrumentation overhead."""
from pathlib import Path
from time import perf_counter
from hybrid_bidirectional_search_v1 import Search as Original
from soft_demand_workspace_stats_bridge_v4 import Search as Forward
from bidirectional_rc_bridge_v1 import Bidirectional
R=Path(__file__).resolve().parents[1]
class RecordedBidirectional(Bidirectional):
    def search(self,source,sink):
        result=super().search(source,sink)
        self.last_counts=None if result is None else dict(scanned_arcs_by_direction=result['scanned_arcs'],settled_nodes_by_direction=result['settled_nodes'])
        return result
class Search(Original):
    def __init__(self,fields,rc,binary):
        self.fields,self.rc=fields,rc
        self.forward=Forward(fields,rc,binary)
        self.bidirectional=RecordedBidirectional(fields,rc,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so')
        self.metrics=[]
    def search(self,source,sinks):
        targets=set(sinks);tick=perf_counter()
        result=super().search(source,targets)
        seconds=perf_counter()-tick
        if len(targets)==1:
            counts=self.bidirectional.last_counts;branch='singleton_bidirectional'
        else:
            counts=dict(self.forward.metrics[-1]);branch='multitarget_forward'
        self.metrics.append(dict(source=source,targets=len(targets),branch=branch,seconds=seconds,counts=counts,counts_available=counts is not None))
        return result
