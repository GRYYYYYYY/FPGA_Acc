"""Bounded proxy-only budget hypothesis; exact initialized criticality p/q."""
from fractions import Fraction
POLICY='original_budget_plus_ceil_one_minus_criticality_times_floor_v1'
def budget(floor,original,criticality):
    if type(floor) is not int or type(original) is not int or not 0<=floor<=original or original<=0:
        raise ValueError('require nonnegative integer floor and positive original budget >= floor')
    if not isinstance(criticality,Fraction) or not 0<=criticality<=1:
        raise ValueError('criticality must be exact Fraction in [0,1]')
    p,q=criticality.numerator,criticality.denominator
    return original+((q-p)*floor+q-1)//q
