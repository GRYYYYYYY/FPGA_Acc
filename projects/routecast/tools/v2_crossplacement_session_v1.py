"""Managed, serial leases over the existing V2 persistent model session.

Original graph/net/CID/type/base guards and V2 model policy remain authoritative.
Owned read-only graph columns; current per-episode inputs are always reread.
Any execution failure closes the backend; no competing recovery or silent rebind.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from dataclasses import dataclass
from types import MappingProxyType
from compact_persistent_native_model_session_v1 import Session as Original
from run_native_endpoint_v2_feedback_v1_2026_10_18 import predict
from mmc_design_core_v1 import seal
from source_binding_v2 import closure
from pre_route_endpoints import sha

@dataclass(frozen=True,slots=True)
class Ticket:
    generation:int
    endpoint:str
    digest:str

class Session(Original):
    def __init__(self,endpoint,*,predictor=predict):
        self._reservation=None;self._busy=False;self.generation=0;self._predictor=predictor
        try:
            super().__init__(endpoint)
            self.nodes,self.fields,self.rc=seal(self.nodes,self.fields,self.rc)
            self.net_names=MappingProxyType(dict(self.net_names));self.identities=MappingProxyType(dict(self.identities))
            self.sources=MappingProxyType({**self.sources,**closure([Path(__file__)])})
        except BaseException:
            if hasattr(self,'search'):self.search.close()
            self.closed=True;raise
    def reserve(self,endpoint):
        if self.closed or self.active or self._reservation is not None:raise RuntimeError('closed or occupied design session')
        p=Path(endpoint).resolve();self.generation+=1;self._reservation=Ticket(self.generation,str(p),sha(p));return self._reservation
    def _ticket(self,ticket):
        if self.closed or ticket is not self._reservation:raise RuntimeError('stale design ticket')
    def cancel(self,ticket):
        self._ticket(ticket)
        if self.active or self._busy:raise RuntimeError('active model execution')
        self._reservation=None
    def acquire(self,endpoint):
        if not self._busy or self._reservation is None:raise RuntimeError('no reserved model execution')
        p=Path(endpoint).resolve()
        if str(p)!=self._reservation.endpoint or sha(p)!=self._reservation.digest:raise ValueError('reserved endpoint changed')
        return super().acquire(endpoint)
    def execute(self,ticket,output,node_base_proof,criticality_directory,warm_directory,scheduling='local'):
        self._ticket(ticket)
        if self._busy:raise RuntimeError('nested model execution')
        self._busy=True
        try:
            if sha(ticket.endpoint)!=ticket.digest:raise ValueError('reserved endpoint changed')
            self.search.total_stats=[0,0,0];self.search.last_stats=None
            result=self._predictor(ticket.endpoint,output,node_base_proof,criticality_directory,warm_directory,scheduling,session=self)
            if self.active or self.search.closed:raise RuntimeError('model did not release its design lease')
            return result
        except BaseException:
            self.close();raise
        finally:self._busy=False;self._reservation=None
    def close(self):
        if not getattr(self,'closed',False):super().close()
        self._reservation=None;self._busy=False
