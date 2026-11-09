"""Fast net pressure with redundant construction-only base adjacency released."""
from fast_normalized_rc_net_pressure import FastNormalizedRCNetPressure
class SlimFastNormalizedRCNetPressure(FastNormalizedRCNetPressure):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  # query uses self.arcs, base.graph and base.node_budget exclusively.
  del self.base.outgoing
