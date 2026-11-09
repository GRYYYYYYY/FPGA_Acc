"""Necessary unique-NET capacity bounds on verified RR vertex separators.

For a cut after coordinate k, start with all nodes whose original bbox spans k.
For each otherwise crossing directed edge, additionally include its destination.
The resulting separator membership for destination v is one interval:
[min(lo[v], min predecessor hi), max(hi[v], max predecessor lo)).
Thus all cuts can be represented with interval difference events in O(V+E+pins),
without assuming RR arcs obey Manhattan geometry or counting oneNET per sink.
A positive excess certifies infeasibility under the supplied endpoint/capacity
model; absence of an excess does not certify routability or native convergence.
"""
from array import array
from collections import Counter

def profile(lows,highs,edges,capacities,NET_terminals):
 n=len(lows)
 if not n or len(highs)!=n or len(capacities)!=n:raise ValueError('node domain')
 if any(type(a) is not int or type(b) is not int or not 0<=a<=b<2**32 for a,b in zip(lows,highs)):raise ValueError('coordinate domain')
 if any(type(c) is not int or c<0 for c in capacities):raise ValueError('capacity domain')
 lower=array('I',lows);upper=array('I',highs);edge_count=0
 for u,v in edges:
  if type(u) is not int or type(v) is not int or not 0<=u<n or not 0<=v<n:raise ValueError('edge domain')
  lower[v]=min(lower[v],highs[u]);upper[v]=max(upper[v],lows[u]);edge_count+=1
 cap_events=Counter();demand_events=Counter();intervals={};knots={min(lows),max(highs)}
 for a,b,c in zip(lower,upper,capacities):
  if a<b:cap_events[a]+=c;cap_events[b]-=c;knots.update([a,b])
 for net,terminals in NET_terminals.items():
  terminals=set(terminals)
  if not terminals or any(type(t) is not int or not 0<=t<n for t in terminals):raise ValueError('terminal domain')
  a=min(lower[t] for t in terminals);b=max(upper[t] for t in terminals);intervals[net]=(a,b)
  if a<b:demand_events[a]+=1;demand_events[b]-=1;knots.update([a,b])
 rows=[];cap=demand=0;end=max(highs)
 for k in sorted(knots):
  cap+=cap_events[k];demand+=demand_events[k];assert cap>=0 and demand>=0
  if k<end:rows.append(dict(cut_after_coordinate=k,separator_capacity=cap,mandatory_unique_NETs=demand,excess=demand-cap))
 assert cap==demand==0
 return dict(lower=lower,upper=upper,NET_intervals=intervals,cuts=rows,edge_count=edge_count,any_capacity_infeasibility_certificate=any(x['excess']>0 for x in rows),scope='Necessary relaxed physical capacity bound only. Requires independently authenticated complete nonignored NET terminals; no route/STA/failure-policy equivalence or routability guarantee from a nonpositive bound.')
