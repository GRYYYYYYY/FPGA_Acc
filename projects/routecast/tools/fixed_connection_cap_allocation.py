"""Fixed search caps; actual complete candidate timing/native gates mandatory."""
from fractions import Fraction as F

def allocate_budget(floor, expanded, initial, target, restrictions, supported, evaluate):
    value=evaluate(floor)
    valid=supported and value<=target and all(floor[c]<=1 for c in expanded)
    # Retained reference paths may exceed 1ns; keep their existing planning
    # value in the reporting envelope. Actual reroute queries retain 1ns cap.
    budgets={c:F(1) if c in expanded else max(F(1),v) for c,v in floor.items()} if valid else {}
    return value,valid,budgets,'FIXED_CONNECTION_CAP_ACTUAL_POSTCHECK',None
