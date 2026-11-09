"""Development oracle-free screening using published live state only.

Maximum connection expansion RC is a proxy, not STA critical path delay. No
nonregression guarantee versus a newly cold-routed target is implied.
"""
from fractions import Fraction

def screen(old,new):
 reasons=[]
 if new['channel_union_wirelength']>old['channel_union_wirelength']:reasons.append('MODEL_WIRE_REGRESSION')
 if Fraction(new['max_connection_rc_seconds'])>Fraction(old['max_connection_rc_seconds']):reasons.append('MODEL_MAX_CONNECTION_RC_REGRESSION')
 return dict(model_admitted=not reasons,reasons=reasons)
