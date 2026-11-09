"""Bounded conflict branching over per-owner forbidden resources.

assess returns None for a feasible state, or a disjunction of (owner,resource)
uses at least one of which must change. reroute returns None only for a proven
infeasible owner under the accumulated forbiddances. Limits are not UNSAT.
"""
import heapq,time

def search(initial,assess,reroute,score,max_states=32,max_queries=64,max_seconds=45):
 start=time.perf_counter();serial=0;heap=[(score(initial),serial,{},initial)];seen={tuple()};events=[];queries=0;expanded=0
 while heap and expanded<max_states and queries<max_queries and time.perf_counter()-start<max_seconds:
  _,sid,masks,trees=heapq.heappop(heap);expanded+=1;conflict=assess(trees)
  if conflict is None:return dict(status='FEASIBLE',trees=trees,masks=masks,events=events,expanded=expanded,queries=queries,seconds=time.perf_counter()-start)
  conflict=sorted(set(conflict));events.append(dict(state=sid,conflict=conflict))
  for owner,resource in conflict:
   if queries>=max_queries or time.perf_counter()-start>=max_seconds:break
   assert resource in trees[owner]['support'] and resource not in masks.get(owner,frozenset())
   child=dict(masks);child[owner]=masks.get(owner,frozenset())|{resource};key=tuple((o,tuple(sorted(rs))) for o,rs in sorted(child.items()))
   if key in seen:continue
   seen.add(key);queries+=1;tree=reroute(owner,child[owner]);serial+=1
   if tree is None:events.append(dict(state=serial,parent=sid,forbidden=[owner,resource],pruned=True));continue
   assert not tree['support'].intersection(child[owner]);next_trees=dict(trees);next_trees[owner]=tree;heapq.heappush(heap,(score(next_trees),serial,child,next_trees));events.append(dict(state=serial,parent=sid,forbidden=[owner,resource],pruned=False))
 status='EXHAUSTED_FIXED_DOMAIN' if not heap and queries<max_queries and time.perf_counter()-start<max_seconds else 'LIMIT_REACHED'
 return dict(status=status,events=events,expanded=expanded,queries=queries,frontier=len(heap),seconds=time.perf_counter()-start)
