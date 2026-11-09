"""Input-only saturated-witness expansion and bounded whole-NET joint repair."""
import time,heapq,copy
from collections import defaultdict,Counter
from joint_owner_constraints_v1 import joint_route
from budget_owner_screen_v2 import screen,witness_in_domain

def constrained_witness(f,rc,q,forbidden,deadline=None):
 src,sink=q['source'],q['sink']
 if src in forbidden or sink in forbidden or f['capacities'][src]<=0:return None
 dist={src:rc.initial(src)};back={};heap=[(dist[src],src)];pops=0
 while heap:
  d,u=heapq.heappop(heap)
  if d!=dist[u]:continue
  pops+=1
  if pops%1024==0 and deadline is not None and time.perf_counter()>=deadline:raise TimeoutError('expansion witness deadline')
  if u==sink:
   path=[];v=sink
   while v!=src:v,e=back[v];path.append(e)
   path.reverse();assert rc.path(src,sink,path)==d;return dict(minimum_integer=d,physical_edge_ids=path)
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if v in forbidden or f['capacities'][v]<=0:continue
   nd=d+rc.increments[s]
   if v not in dist or nd<dist[v]:dist[v]=nd;back[v]=(u,f['edge_ids'][s]);heapq.heappush(heap,(nd,v))
 return None

def repair(f,rc,before,query,initial_release,floors,spans,penalty,global_required,remaining_cache=None,max_owner_nets=4,max_release_attempts=4,max_joint_nodes=32,deadline=None,observer=None,max_owner_checks=32,max_screens=4):
 if any(type(v) is not int or v<1 for v in (max_owner_nets,max_release_attempts,max_joint_nodes,max_owner_checks,max_screens)):raise ValueError('positive repair limits required')
 before=copy.deepcopy(before);slots={e:s for s,e in enumerate(f['edge_ids'])};counts=Counter(r['net_id'] for r in before);initial=frozenset(initial_release)
 if not initial or len(initial)>max_owner_nets or any(net not in counts for net in initial):raise ValueError('invalid initial owner release')
 if any(r['connection_id']==query['connection_id'] for r in before):raise ValueError('query already accepted')
 pending=[initial];seen={initial};attempts=[];solution=None;chosen=None;owner_checks=0;screens=0
 while pending and len(attempts)<max_release_attempts and (deadline is None or time.perf_counter()<deadline):
  release=pending.pop(0);kept=[r for r in before if r['net_id'] not in release];removed=[r for r in before if r['net_id'] in release];groups=defaultdict(list)
  for r in sorted(removed,key=lambda r:(r['net_id'],r['connection_id'])):groups[r['net_id']].append({k:r[k] for k in ('connection_id','net_id','source','sink')})
  groups[query['net_id']].insert(0,query);idx=len(attempts)
  def observe(entry,states,found):
   if observer is not None:observer(idx,sorted(release),entry,states,found)
  result=joint_route(f,rc,dict(groups),floors,kept,spans,penalty,global_required,remaining_cache=remaining_cache,max_joint_nodes=max_joint_nodes,deadline=deadline,observer=observe);evidence=[];entry=dict(index=idx,released_net_ids=sorted(release),removed_connection_ids=[r['connection_id'] for r in removed],joint_status=result['status'],branches=result['branches'],expansion_evidence=evidence,fallback_evidence=[])
  attempts.append(entry)
  if result['solution'] is not None:solution=result['solution'];chosen=sorted(release);break
  owners=defaultdict(set)
  for r in kept:owners[r['net_id']].add(r['source']);owners[r['net_id']].update(f['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
  for branch in result['branches']:
   for netstr,failure in branch['failures'].items():
    if failure is None or failure['status']!='NO_BUDGET_CAPACITY_PATH':continue
    net=int(netstr);forbidden=frozenset(n for owner,n in branch['constraints'] if owner==net)
    if not forbidden:continue
    try:witness=constrained_witness(f,rc,failure['query'],forbidden,deadline)
    except TimeoutError:entry['expansion_deadline']=True;break
    if witness is None or witness['minimum_integer']>failure['budget_integer']:continue
    other=Counter(n for owner,own in owners.items() if owner!=net for n in own);used={failure['query']['source']}|{f['dest_ranks'][slots[e]] for e in witness['physical_edge_ids']};blocked=sorted(n for n in used if other[n]>=f['capacities'][n]);blockers=sorted(owner for owner,own in owners.items() if owner!=net and own.intersection(blocked));expanded=release|set(blockers);evidence.append(dict(query=failure['query'],forbidden_nodes=sorted(forbidden),witness=witness,budget_integer=failure['budget_integer'],blocked_nodes=blocked,blocking_net_ids=blockers,expanded_release=sorted(expanded)))
    if blockers and len(expanded)<=max_owner_nets and expanded not in seen:seen.add(expanded);pending.append(expanded)
    if len(expanded)>max_owner_nets and len(release)<max_owner_nets and screens<max_screens and owner_checks<max_owner_checks:
     try:
      domain=screen(f,rc,failure['query'],forbidden,owners,failure['budget_integer'],deadline);screens+=1;baseline=witness_in_domain(f,rc,failure['query'],domain,other,set(),failure['budget_integer'],deadline);fallback=dict(query=failure['query'],budget_integer=failure['budget_integer'],forbidden_nodes=sorted(forbidden),domain=domain,baseline=baseline,checks=[]);entry['fallback_evidence'].append(fallback)
      if baseline is not None:fallback['status']='BASELINE_ALREADY_FEASIBLE_NOT_FILTERED';continue
      fallback['status']='BASELINE_FAILED_FILTER_VALID'
      for extra in sorted(domain['candidates'],key=lambda owner:(counts[owner],owner)):
       if owner_checks>=max_owner_checks:break
       owner_checks+=1;alternative=witness_in_domain(f,rc,failure['query'],domain,other,owners[extra],failure['budget_integer'],deadline);expanded_one=release|{extra};fallback['checks'].append(dict(extra_net=extra,witness=alternative,expanded_release=sorted(expanded_one)))
       if alternative is not None and expanded_one not in seen:seen.add(expanded_one);pending.append(expanded_one)
     except TimeoutError:entry['fallback_deadline']=True;break
  pending.sort(key=lambda ns:(sum(counts[n] for n in ns),len(ns),tuple(sorted(ns))))
 status='FOUND_JOINT_BATCH' if solution is not None else 'DEADLINE' if deadline is not None and time.perf_counter()>=deadline else 'RELEASE_ATTEMPT_LIMIT' if pending else 'REPAIR_EXHAUSTED'
 return dict(status=status,solution=solution,released_net_ids=chosen,attempts=attempts,remaining_release_sets=[sorted(ns) for ns in pending],owner_checks=owner_checks,screens=screens,scope='Bounded input-only repair. Caller owns global transaction/cache finalize; no general completeness.')
