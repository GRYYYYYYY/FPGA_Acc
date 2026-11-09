"""Owned price snapshot, weighted once per prepare; exact legacy search ordering."""
import ctypes as C
from soft_demand_workspace_stats_bridge_v4 import Search as Original

class Search(Original):
    def __init__(self, *args):
        super().__init__(*args)
        self.lib.rc_tree_workspace_prepriced.argtypes = self.lib.rc_tree_workspace.argtypes
        self.lib.rc_tree_workspace_prepriced.restype = C.c_int
        self.lib.rc_workspace_prepare_prices.argtypes = [C.c_void_p, C.c_uint64, C.c_uint64, C.POINTER(C.c_uint64)]
        self.lib.rc_workspace_prepare_prices.restype = C.c_int

    def prepare(self, prices, weight):
        # prepare owns the array; callers must not mutate it between prepares.
        super().prepare(prices, weight)
        code = self.lib.rc_workspace_prepare_prices(self.handle, self.n, self.weight, self.ptr(self.price))
        if code:
            raise RuntimeError(f'prepared price status {code}')

    def _run(self, *args):
        if not self.handle:
            raise RuntimeError('workspace closed')
        return self.lib.rc_tree_workspace_prepriced(self.handle, *args)
