"""Candidate-local breadth-first detour exploration; caller owns restoration/gates."""
import heapq
from online_conflict_core import detour_options

def bounded_conflict_branches(initial,attempt,observe,allocate,max_attempts=4,max_frontier=32):
    if type(max_attempts) is not int or max_attempts<1 or type(max_frontier) is not int or max_frontier<1:
        raise ValueError('positive integer bounds required')
    initial={k:set(v) for k,v in initial.items()};first=allocate(initial)
    if first is None:return dict(status='INITIAL_ALLOCATION_REJECTED',trace=[])
    frontier=[(0,first[0],0,initial,first[1],None)];sequence=1;trace=[];seen={tuple((k,tuple(sorted(v))) for k,v in sorted(initial.items()))};dropped=0
    def queue_snapshot():
        return [dict(depth=x[0],score=[str(v) for v in x[1]] if isinstance(x[1],tuple) else [str(x[1])],order=x[2],parent=x[5],restrictions={k:sorted(v) for k,v in x[3].items()},allocation_index=x[4].get('index')) for x in sorted(frontier,key=lambda x:x[:3])]
    while frontier and len(trace)<max_attempts:
        before=queue_snapshot()
        depth,score,order,restrictions,spec,parent=heapq.heappop(frontier)
        candidate=attempt(restrictions,spec);index=len(trace)
        entry=dict(iteration=index,depth=depth,parent=parent,queue_before=before,queue_order=order,frontier_evictions=[],restrictions={k:sorted(v) for k,v in restrictions.items()},candidate=candidate);trace.append(entry)
        if (candidate.get('failure') or {}).get('status')=='PREFIX_MODEL_TIMING_REJECTED':
            return dict(status='PREFIX_MODEL_TIMING_REJECTED',trace=trace,candidate=candidate,dropped_frontier=dropped)
        if candidate.get('failure') is None and candidate['completed_connections']==candidate['required_connections']:
            return dict(status='COMPLETE_CANDIDATE',trace=trace,candidate=candidate,dropped_frontier=dropped)
        if len(trace)==max_attempts:break
        observation=observe(candidate,restrictions,spec);entry['observation']=observation;entry['options']=[]
        for option in detour_options(observation,restrictions):
            key=tuple((k,tuple(sorted(v))) for k,v in sorted(option.items()))
            if key in seen:
                entry['options'].append(dict(restrictions={k:sorted(v) for k,v in option.items()},status='DUPLICATE'));continue
            seen.add(key);result=allocate(option)
            if result is None:status='ALLOCATION_REJECTED'
            else:
                heapq.heappush(frontier,(depth+1,result[0],sequence,option,result[1],index));sequence+=1;status='QUEUED'
                if len(frontier)>max_frontier:
                    worst=max(range(len(frontier)),key=lambda n:frontier[n][:3]);removed=frontier.pop(worst);entry['frontier_evictions'].append(removed[2]);heapq.heapify(frontier);dropped+=1
            entry['options'].append(dict(restrictions={k:sorted(v) for k,v in option.items()},status=status))
        entry['queue_after']=queue_snapshot()
    return dict(status='ATTEMPT_LIMIT' if len(trace)==max_attempts else 'FRONTIER_EXHAUSTED',trace=trace,candidate=trace[-1]['candidate'],dropped_frontier=dropped)
