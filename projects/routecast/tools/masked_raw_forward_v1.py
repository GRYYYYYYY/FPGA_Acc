"""Exact raw-only forward search with serial hard node masks and copied certificates.

Uses the existing checked 128-bit ABI. The cap array is read by the forward
backend on each call (unlike the bidirectional backend's copied capacities).
All temporary capacities are restored even when the query fails.
"""
from wide_cost_search_bridge_v2 import Forward

class Search:
    def __init__(self,fields,rc,binary):
        self.engine=Forward(fields,rc,binary);self.engine.prepare({},0);self.caps=tuple(self.engine.cap)
    def query(self,source,sinks,blocked):
        e=self.engine;targets=set(sinks);blocked=frozenset(blocked)
        if not targets:raise ValueError('nonempty target set required')
        for n in {source}|targets|blocked:
            if type(n) is not int or not 0<=n<e.n:raise ValueError('node domain')
        if source in blocked or targets&blocked or any(not self.caps[n] for n in {source}|targets):raise ValueError('disabled/blocked endpoint')
        try:
            for n in blocked:e.cap[n]=0
            raw,parents,reached=e.search(source,targets);answers={}
            for sink in sorted(targets):
                if sink not in reached:answers[sink]={'reachable':False};continue
                u=sink;slots=[];seen={u}
                while u!=source:
                    previous,slot=parents[u]
                    if previous in seen:raise ValueError('cyclic predecessor')
                    slots.append(int(slot));seen.add(previous);u=previous
                slots.reverse();answers[sink]={'reachable':True,'minimum':raw[sink],'slots':slots}
            cutoff=max(raw[n] for n in range(e.n) if e.settled[n])
            return {'answers':answers,'cutoff':cutoff,'initial':e.initial[source],'settled_bytes':e.settled.tobytes(),'raw_u128_bytes':bytes(e.raw.buffer)}
        finally:
            for n in blocked:e.cap[n]=self.caps[n]
    def close(self):self.engine.close()
