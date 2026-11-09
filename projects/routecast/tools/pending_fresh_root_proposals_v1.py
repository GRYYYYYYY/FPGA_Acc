"""Bounded candidate releases screened on all selected fresh-root ordinary conditions."""
import copy
from collections import Counter,defaultdict
from budget_owner_screen_v2 import screen
from fresh_release_root_screen_v2 import FreshRootScreen

def propose(fields,rc,before,release,queries,floors,deadline=None,max_domains=4,max_checks=128,max_candidates=4):
 if any(type(v) is not int or v<1 for v in (max_domains,max_checks,max_candidates)):raise ValueError('positive limits required')
 queries=copy.deepcopy(list(queries));context=FreshRootScreen(fields,rc,before,floors);release=frozenset(release)
 if not release or not release<=context.owners.keys():raise ValueError('invalid initial release')
 initial=context.check(release,queries,deadline)
 counts=Counter(record['net_id'] for record in before);kept={net:nodes for net,nodes in context.owners.items() if net not in release};domains=[];extras=set()
 for query in queries[:max_domains]:
  floor=context.floors[(query['source'],query['sink'])];budget=max(context.rc.scale//10**9,(3*floor+1)//2);domain=screen(context.fields,context.rc,query,frozenset(),kept,budget,deadline);domains.append(dict(query=dict(query),budget=budget,domain=domain));extras.update(domain['candidates'])
 candidates={(release-{old})|{extra} for old in release for extra in extras if extra not in release};ordered=sorted(candidates,key=lambda owners:(sum(counts[net] for net in owners),tuple(sorted(owners))));checks=[];accepted=[]
 for candidate in ordered[:max_checks]:
  result=context.check(candidate,queries,deadline);checks.append(result)
  if result['all_selected_ordinary_budget_feasible']:accepted.append(sorted(candidate))
  if len(accepted)>=max_candidates:break
 return dict(initial_root=initial,domains=domains,checks=checks,proposed=accepted,scope='Input-only selected-query budget-domain owner swaps; all selected fresh-root ordinary conditions are necessary, not sufficient. One old/extra swap, same release cardinality, bounded domain/candidate coverage, no general solver completeness or native-quality guarantee.')
