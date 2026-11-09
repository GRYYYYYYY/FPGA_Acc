"""Compare sparse guarded shortest paths with an independent simple-path oracle."""
import itertools,json
from occupied_tree_delay_search import search

def main():
 cases=0;pairs=[(u,v) for u in range(3) for v in range(3) if u!=v]
 for mask in range(1<<len(pairs)):
  graph={n:[] for n in range(3)}
  for i,(u,v) in enumerate(pairs):
   if mask&(1<<i):graph[u].append((v,(u+v)%3))
  for allowed_bits in range(8):
   allowed=lambda n:bool(allowed_bits&(1<<n))
   for fixed in [{},{1:0},{1:2},{2:1}]:
    found=[]
    def walk(path,cost):
     u=path[-1]
     if u==2:found.append((cost,len(path)-1));return
     for v,w in graph[u]:
      if v not in path and allowed(v) and (v not in fixed or fixed[v]==u):walk(path+[v],cost+w)
    if allowed(0) and allowed(2):walk([0],0)
    a=search(graph.__getitem__,allowed,0,2,fixed,maximum_expanded=10)
    if found:assert a['status']=='optimal_additive_delay_path' and (a['delay'],a['hops'])==min(found)
    else:assert a['status']=='no_feasible_path'
    cases+=1
 assert search(lambda n:[(1,1)] if n==0 else [],lambda n:True,0,1,{},1)['status']=='expansion_budget_exhausted'
 print(json.dumps({'status':'guarded_delay_search_oracle_checks_pass','cases':cases,'scope':'Directed3node graphs,zero/positive delay,all occupancy masks,fixed-parent variants; explicit budget exhaustion. Native RC timing and full tree integration unproven.'}))
if __name__=='__main__':main()
