"""Limits for strictly distinct prediction scores against nonconstant binary truth."""
from fractions import Fraction

def limits(n,positives,k):
 if any(type(v) is not int for v in [n,positives,k]) or n<2 or not 0<positives<n or not 1<=k<=n:raise ValueError('nonconstant binary label domain required')
 # No prediction ties. Maximum Spearman is reached by perfect class separation.
 rho_squared=Fraction(3*positives*(n-positives),n*n-1)
 # Among perfect-separation strict orders, topK may choose any K positives,
 # or all positives plus any K-positives negatives when K exceeds positives.
 minimum=max(0,2*k-positives) if k<=positives else positives+max(0,2*(k-positives)-(n-positives))
 return {'maximum_strict_score_spearman_squared':rho_squared,'perfect_separation_minimum_topK_hits':minimum,'perfect_separation_maximum_topK_hits':k}
