"""Finite-state progress rank and exact capacity-witness rollback planning."""
from collections import Counter

def rank(package,selected,protected):
 package=set(package);selected=set(selected);protected=set(protected)
 if not protected<=selected<=package:raise ValueError('state domain')
 n=len(package)
 return (n-len(protected))*(n+1)+(n-len(selected))

def rollback_owners(capacities,outside,ownership,protected,candidate_nodes):
 protected=set(protected);candidate_nodes=set(candidate_nodes)
 if not protected<=set(ownership):raise ValueError('protected NET missing')
 fixed=Counter(n for net in protected for n in ownership[net]);usage=Counter(n for ns in ownership.values() for n in ns)
 if any(outside.get(n,0)+fixed[n]+1>capacities[n] for n in candidate_nodes):raise ValueError('candidate violates protected core')
 blocked={n for n in candidate_nodes if outside.get(n,0)+usage[n]+1>capacities[n]}
 removed=sorted(net for net,ns in ownership.items() if net not in protected and set(ns)&blocked)
 after=Counter(n for net,ns in ownership.items() if net not in removed for n in ns);after.update(candidate_nodes)
 if any(outside.get(n,0)+count>capacities[n] for n,count in after.items()):raise ValueError('invalid starting state or release')
 return removed
