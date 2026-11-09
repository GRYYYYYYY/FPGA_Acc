"""Diagnostic only: independent uniform tie selections, not an acceptance metric."""
from fractions import Fraction

def profile(values,k):
 if not 0<k<=len(values):raise ValueError('k')
 boundary=sorted(values.values(),reverse=True)[k-1];above=sum(v>boundary for v in values.values());tied=sum(v==boundary for v in values.values());fraction=Fraction(k-above,tied)
 probabilities={n:Fraction(1) if v>boundary else fraction if v==boundary else Fraction(0) for n,v in values.items()};assert sum(probabilities.values())==k
 return dict(boundary=str(boundary),above=above,tied=tied,selected_from_tie=k-above),probabilities

def diagnose(prediction,truth,k):
 if set(prediction)!=set(truth):raise ValueError('domain')
 p,pp=profile(prediction,k);t,tp=profile(truth,k);fixedp=set(sorted(prediction,key=lambda n:(-prediction[n],n))[:k]);fixedt=set(sorted(truth,key=lambda n:(-truth[n],n))[:k]);hits=len(fixedp&fixedt);expected=sum((pp[n]*tp[n] for n in truth),Fraction(0))
 return dict(k=k,universe_size=len(truth),prediction=p,truth=t,fixed_ID_hits=hits,fixed_ID_precision=str(Fraction(hits,k)),independent_uniform_tie_expected_hits=str(expected),independent_uniform_tie_expected_precision=str(expected/k),truth_distinct_scores=len(set(truth.values())),prediction_distinct_scores=len(set(prediction.values())))
