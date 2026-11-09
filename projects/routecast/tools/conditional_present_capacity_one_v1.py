"""Advisory capacity-one present replacement; never mutates native state."""
import math,struct
def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
def bits(value):return struct.unpack('<I',struct.pack('<f',value))[0]
def present_bits(capacity,retained_own,future_other_mean,pres_bits):
 if type(capacity) is not int or capacity!=1:raise ValueError('capacity-one contract required')
 if type(retained_own) is not int or retained_own not in [0,1]:raise ValueError('retained membership domain')
 if type(pres_bits) is not int or not 0<=pres_bits<2**32:raise ValueError('present factor word domain')
 pres=struct.unpack('<f',struct.pack('<I',pres_bits))[0]
 if not math.isfinite(pres) or pres<0:raise ValueError('present factor domain')
 mean=float(future_other_mean)
 if not math.isfinite(mean) or mean<0:raise ValueError('other-owner mean domain')
 h=f32(retained_own+f32(mean));value=f32(1.+f32(pres*h))
 if not math.isfinite(value):raise ValueError('nonfinite advisory multiplier')
 return bits(value)
