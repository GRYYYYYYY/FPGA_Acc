"""Resource CBS with preserved frontier and unfinished conflict children."""
import heapq,time
class SearchBudgetExceeded(Exception):pass

def mask_key(masks):return tuple((n,tuple(sorted(rs))) for n,rs in sorted(masks.items()) if rs)

def restore_v1(initial,events,query_tree):
 states={0:{'masks':{},'trees':initial}};seen={mask_key({})};processed=[];serial=0
 for e in events:
  sid=e['state'];serial=max(serial,sid)
  if 'parent' not in e:assert sid in states;processed.append((sid,e['conflict']));continue
  parent=states[e['parent']];owner,node=e['forbidden'];masks=dict(parent['masks']);masks[owner]=masks.get(owner,frozenset())|{node};key=mask_key(masks);assert key not in seen;seen.add(key);tree=query_tree(sid,owner,masks[owner]);assert (tree is None)==e['pruned']
  if tree is not None:
   trees=dict(parent['trees']);trees[owner]=tree;states[sid]={'masks':masks,'trees':trees}
 pending=[]
 for sid,conflict in processed:
  remaining=[]
  for owner,node in sorted(set(map(tuple,conflict))):
   masks=dict(states[sid]['masks']);masks[owner]=masks.get(owner,frozenset())|{node}
   if mask_key(masks) not in seen:remaining.append((owner,node))
  if remaining:pending.append({'state':sid,'remaining':remaining})
 assessed={sid for sid,c in processed};frontier=sorted(set(states)-assessed)
 return {'states':states,'seen':seen,'serial':serial,'frontier':frontier,'pending':pending}

def search(initial,assess,reroute,score,max_states=128,max_queries=512,max_seconds=60,checkpoint=None):
 start=time.perf_counter();cp=checkpoint or {'states':{0:{'masks':{},'trees':initial}},'seen':{mask_key({})},'serial':0,'frontier':[0],'pending':[]};states=dict(cp['states']);seen=set(cp['seen']);serial=cp['serial'];pending=[{'state':x['state'],'remaining':list(map(tuple,x['remaining']))} for x in cp['pending']];heap=[(score(states[s]['trees']),s) for s in cp['frontier']];heapq.heapify(heap);events=[];queries=0;expanded=0;reason=None
 while heap or pending:
  if time.perf_counter()-start>=max_seconds:reason='TIME';break
  if not pending:
   if expanded>=max_states:reason='STATES';break
   _,sid=heapq.heappop(heap);state=states[sid];conflict=assess(state['trees']);expanded+=1
   if conflict is None:
    return {'status':'FEASIBLE','trees':state['trees'],'masks':state['masks'],'events':events,'expanded':expanded,'queries':queries,'seconds':time.perf_counter()-start,'checkpoint':None}
   conflict=sorted(set(map(tuple,conflict)));events.append({'state':sid,'conflict':conflict});pending.append({'state':sid,'remaining':list(conflict)})
  task=pending[0];sid=task['state'];state=states[sid]
  if not task['remaining']:pending.pop(0);continue
  owner,node=task['remaining'][0];assert node in state['trees'][owner]['support'] and node not in state['masks'].get(owner,frozenset());masks=dict(state['masks']);masks[owner]=masks.get(owner,frozenset())|{node};key=mask_key(masks)
  if key in seen:task['remaining'].pop(0);continue
  if queries>=max_queries:reason='ROUTE_REQUESTS';break
  try:tree=reroute(owner,masks[owner])
  except SearchBudgetExceeded:reason='RAW_QUERY_BUDGET';break
  queries+=1;serial+=1;seen.add(key);task['remaining'].pop(0);events.append({'state':serial,'parent':sid,'forbidden':[owner,node],'pruned':tree is None})
  if tree is not None:
   assert not tree['support']&masks[owner];trees=dict(state['trees']);trees[owner]=tree;states[serial]={'masks':masks,'trees':trees};heapq.heappush(heap,(score(trees),serial))
 cp={'states':states,'seen':seen,'serial':serial,'frontier':[sid for _,sid in heap],'pending':pending};return {'status':'LIMIT_REACHED' if reason else 'EXHAUSTED_FIXED_DOMAIN','limit_reason':reason,'events':events,'expanded':expanded,'queries':queries,'seconds':time.perf_counter()-start,'checkpoint':cp}
