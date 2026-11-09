"""Heuristic bounded fixed-forbidden swap proposals, not a complete joint filter."""
from collections import Counter,defaultdict
from budget_owner_screen_v2 import screen,witness_in_domain

def propose(f,rc,before,release,branches,deadline=None,max_domains=4,max_checks=32,max_candidates=4):
 if any(type(v) is not int or v<1 for v in (max_domains,max_checks,max_candidates)):raise ValueError('positive proposal limits required')
 release=set(release)
 if not release:raise ValueError('nonempty released NETs required')
 slots={e:s for s,e in enumerate(f['edge_ids'])};allowners=defaultdict(set)
 for r in before:allowners[r['net_id']].add(r['source']);allowners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
 keptowners={net:own for net,own in allowners.items() if net not in release};counts=Counter(r['net_id'] for r in before);domains=[];checks=[];proposals=set();seen=set()
 for branch in branches:
  for netstr,failure in branch['failures'].items():
   if failure is None or failure['status']!='NO_BUDGET_CAPACITY_PATH':continue
   q=failure['query'];banned=frozenset(n for net,n in branch['constraints'] if net==int(netstr));key=(q['connection_id'],banned)
   if key in seen or len(domains)>=max_domains:continue
   seen.add(key);domain=screen(f,rc,q,banned,keptowners,failure['budget_integer'],deadline);other=Counter(n for net,own in keptowners.items() if net!=q['net_id'] for n in own);baseline=witness_in_domain(f,rc,q,domain,other,set(),failure['budget_integer'],deadline);entry=dict(query=q,budget=failure['budget_integer'],banned=sorted(banned),domain=domain,baseline=baseline);domains.append(entry)
   if baseline is not None:continue
   pairs=sorted(((old,extra) for extra in domain['candidates'] for old in release),key=lambda pair:(sum(counts[n] for n in (release-{pair[0]})|{pair[1]}),pair[1],pair[0]))
   for old,extra in pairs:
    if len(checks)>=max_checks:break
    restored=other.copy()
    if old!=q['net_id']:restored.update(allowners[old])
    witness=witness_in_domain(f,rc,q,domain,restored,allowners[extra],failure['budget_integer'],deadline);candidate=(release-{old})|{extra};checks.append(dict(domain=len(domains)-1,old=old,extra=extra,release=sorted(candidate),witness=witness))
    if witness is not None:proposals.add(frozenset(candidate))
 ordered=sorted(proposals,key=lambda owners:(sum(counts[n] for n in owners),tuple(sorted(owners))))[:max_candidates];
 return dict(domains=domains,checks=checks,proposed=[sorted(ns) for ns in ordered],scope='Fixed-forbidden ordinary-capacity swap witnesses are heuristic proposals for fresh joint roots; not general necessary filter or joint feasibility.')
