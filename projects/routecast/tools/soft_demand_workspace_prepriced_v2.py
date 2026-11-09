"""Owned per-prepare 128-bit node-price products, unchanged search interface."""
import ctypes as C
from soft_demand_workspace_bridge_v1 import Search as Original

class Search(Original):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lib.rc_workspace_prepare_price.argtypes = [C.c_void_p, C.c_uint64, C.c_uint64, C.POINTER(C.c_uint64)]
        self.lib.rc_workspace_prepare_price.restype = C.c_int

    def prepare(self, prices, weight):
        super().prepare(prices, weight)
        status = self.lib.rc_workspace_prepare_price(self.handle, self.n, self.weight, self.ptr(self.price))
        if status:
            raise RuntimeError(f'owned price preparation status {status}')
