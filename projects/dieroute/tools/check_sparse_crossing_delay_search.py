"""Independent simple-path oracle for capacity/parent/crossing constrained delay."""
import json
from sparse_crossing_delay_search import search

def main():
 pairs=[(u,v) for u in range(3) for v in range(3) if u!=v];cases=0;die=[0,1,0]
 for mask in range(64):
  graph={n:[] for n in range(3)}
  for i,(u,v) in enumerate(pairs):
   if mask&(1<<i):graph[u].append((v,(u+v)%3))
  for bits in range(8):
   allowed=lambda n:bool(bits&(1<<n))
   for fixed in [{},{1:0},{1:2},{2:1}]:
    def adjacency(u):return [(v,w,int(die[u]!=die[v] and v not in fixed)) for v,w in graph[u]]
    for budget in range(3):
     found=[]
     def walk(path,delay,cross):
      u=path[-1]
      if u==2:found.append((delay,len(path)-1));return
      for v,w,charge in adjacency(u):
       if v not in path and allowed(v) and (v not in fixed or fixed[v]==u) and cross+charge<=budget:walk(path+[v],delay+w,cross+charge)
     if allowed(0) and allowed(2):walk([0],0,0)
     answer=search(adjacency,allowed,0,2,fixed,budget,100)
     if found:assert answer['status']=='optimal_bounded_delay_path' and (answer['delay'],answer['hops'])==min(found) and answer['crossings']<=budget
     else:assert answer['status']=='no_feasible_path'
     cases+=1
 assert search(lambda n:[(1,1,0)],lambda n:True,0,1,{},0,1)['status']=='label_budget_exhausted'
 print(json.dumps({'status':'sparse_crossing_delay_search_oracle_checks_pass','cases':cases,'scope':'Directed3nodegraphs,occupancymasks,fixedparents,crossingbudgets;independentsimplepathoracle. Notnativequalityorfulltreeproof.'}))
if __name__=='__main__':main()
