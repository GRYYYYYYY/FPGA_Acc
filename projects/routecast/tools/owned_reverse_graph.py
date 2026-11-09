"""Explicit owned immutable graph handle; costs/capacity/demand stay query-local."""
import ctypes
from pathlib import Path

class OwnedReverseGraph:
    def __init__(self, n, m, rows, dest, edges, increments, library):
        self.lib = ctypes.CDLL(str(library))
        Q = ctypes.c_uint64
        P = ctypes.POINTER(Q)
        self.lib.rc_graph_create.argtypes = [Q,Q,P,P,P,P,P]
        self.lib.rc_graph_create.restype = ctypes.c_int
        self.lib.rc_graph_destroy.argtypes = [Q]
        self.lib.rc_graph_destroy.restype = ctypes.c_int
        self.lib.rc_graph_query.argtypes = [Q,P,P,P,*([Q]*7),P,P]
        self.lib.rc_graph_query.restype = ctypes.c_int
        handle = Q()
        code = self.lib.rc_graph_create(n,m,rows,dest,edges,increments,ctypes.byref(handle))
        if code != 0:
            raise ValueError(f'graph creation failed: {code}')
        self.handle = handle.value
        self.n = n

    def bridge(self, n, rows, dest, edges, costs, capacities, increments, other,
               source, sink, initial_lo, initial_hi, budget_lo, budget_hi,
               limit, path, result):
        # Adapter for the existing wrapper: graph arrays are snapshot inputs;
        # the explicit owned API never reads them again after construction.
        if n != self.n:
            for i in range(8):
                result[i] = 0
            return 4
        return self.lib.rc_graph_query(self.handle,costs,capacities,other,
               source,sink,initial_lo,initial_hi,budget_lo,budget_hi,limit,path,result)

    def close(self):
        if self.handle:
            code = self.lib.rc_graph_destroy(self.handle)
            if code != 0:
                raise RuntimeError('graph release failed')
            self.handle = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
