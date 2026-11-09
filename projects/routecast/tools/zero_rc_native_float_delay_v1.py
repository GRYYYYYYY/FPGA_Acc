"""Native float32 RR delay recurrence for a separately certified zero-R/C graph.

Integer-lattice budget accounting remains separate. This is not an RC-tree model.
"""
import math,struct

def f32(value):
 return struct.unpack('f',struct.pack('f',value))[0]

def switch_path_delay(switch_ids,switch_delays_s):
 """SOURCE arrival zero; round every switch addition exactly as native float."""
 delay=f32(0.0)
 for switch in switch_ids:
  increment=f32(switch_delays_s[switch])
  if not math.isfinite(increment) or increment<0:raise ValueError('invalid switch delay')
  delay=f32(delay+increment)
  if not math.isfinite(delay):raise ValueError('delay overflow')
 return delay
