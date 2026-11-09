"""Serial expansion-limited searches; missing targets have no infeasibility proof."""
import ctypes as C
from soft_demand_workspace_bridge_v1 import Search as Original

class Search(Original):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.limit = None
        self.lib.rc_tree_workspace_limited.argtypes = [C.c_void_p, *self.lib.rc_tree_workspace.argtypes[1:], C.c_uint64]
        self.lib.rc_tree_workspace_limited.restype = C.c_int

    def _run(self, *args):
        if not self.handle:
            raise RuntimeError('workspace closed')
        if self.limit is None:
            return self.lib.rc_tree_workspace(self.handle, *args)
        return self.lib.rc_tree_workspace_limited(self.handle, *args, self.limit)

    def search(self, source, sinks, expansion_limit=None):
        if expansion_limit is not None and (type(expansion_limit) is not int or not 0 <= expansion_limit < 2**64):
            raise ValueError('invalid expansion limit')
        self.limit = expansion_limit
        try:
            return super().search(source, sinks)
        finally:
            self.limit = None
