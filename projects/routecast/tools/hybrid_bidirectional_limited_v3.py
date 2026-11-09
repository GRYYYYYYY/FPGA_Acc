"""Requested-path interface only; no all-node array or tree footprint equivalence."""
from pathlib import Path
from soft_demand_workspace_limited_v3 import Search as Forward
from bidirectional_rc_bridge_v1 import Bidirectional
R=Path(__file__).resolve().parents[1]
class Search:
    def __init__(self,fields,rc,binary):
        self.fields,self.rc=fields,rc
        self.phase=-1
        self.forward=Forward(fields,rc,binary)
        self.bidirectional=Bidirectional(fields,rc,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so')
    def prepare(self,prices,weight):
        self.forward.prepare(prices,weight)
        self.bidirectional.prepare(prices,weight)
        self.phase+=1
    def search(self,source,sinks):
        targets=set(sinks)
        self.last_metadata=dict(expansion_limit=4096 if self.phase>0 and len(targets)>1 else None, missing_targets_are_infeasible=False)
        if len(targets)!=1:
            result=self.forward.search(source,targets,expansion_limit=self.last_metadata["expansion_limit"])
            self.last_metadata["settled_targets"]=sorted(result[2])
            return result
        sink=next(iter(targets));answer=self.bidirectional.search(source,sink)
        self.last_metadata["settled_targets"]=[] if answer is None else [sink]
        if answer is None:return {},{},set()
        u=source;parents={}
        for slot in answer['slots']:
            v=self.fields['dest_ranks'][slot]
            assert self.fields['row_offsets'][u]<=slot<self.fields['row_offsets'][u+1]
            assert v not in parents and v!=source
            parents[v]=(u,slot);u=v
        assert u==sink
        return {source:self.rc.initial(source),sink:answer['raw']},parents,{sink}
    def close(self):
        if hasattr(self,'forward'):self.forward.close()
        if hasattr(self,'bidirectional'):self.bidirectional.close()
    def __del__(self):self.close()
