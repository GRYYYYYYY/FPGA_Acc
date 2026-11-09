"""Necessary Hall capacity gate; caller authenticates complete reachable sets.

One obligation per distinct NET for the same terminal sink. A positive result
means no cut found, not complete routing feasibility. Serial preflight wrapper.
"""
import itertools

def terminal_cut(obligations,capacities,max_nets=16):
 if type(max_nets) is not int or max_nets<1:raise ValueError('positive subset limit required')
 captured=[];nets=set()
 for net,pins in obligations:
  if type(net) is not int or net<0 or net in nets:raise ValueError('distinct NET obligations required')
  nodes=frozenset(pins)
  if any(type(n) is not int or n<0 for n in nodes):raise ValueError('invalid terminal node')
  nets.add(net);captured.append((net,nodes))
 values={}
 for net,pins in captured:
  for node in pins:
   value=capacities[node]
   if type(value) is not int or value<0:raise ValueError('exact nonnegative capacity required')
   values[node]=value
 if len(captured)>max_nets:return {'status':'UNKNOWN','reason':'subset_limit','net_count':len(captured)}
 captured.sort()
 for count in range(1,len(captured)+1):
  for subset in itertools.combinations(captured,count):
   pins=set().union(*(s for net,s in subset));available=sum(values[n] for n in pins)
   if available<count:return {'status':'INFEASIBLE','nets':[net for net,s in subset],'terminal_nodes':sorted(pins),'available_capacity':available,'required_net_uses':count}
 return {'status':'NO_CUT','net_count':len(captured)}

def commit_with_terminal_preflight(transaction,expected_epoch,preflight,build,validate):
 """Serial only; a cut avoids calling build, ordinary commit owns publication."""
 old=transaction.snapshot()
 if type(expected_epoch) is not int or old.epoch!=expected_epoch:return 'STALE'
 result=preflight(old)
 if result['status']=='INFEASIBLE':return 'INFEASIBLE'
 if result['status'] not in ('NO_CUT','UNKNOWN'):raise ValueError('unsupported preflight status')
 return transaction.commit(expected_epoch,build,validate)
