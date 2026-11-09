"""Independent arbitrary-H heap reference, legacy H0 paths/work and tree purity."""
import json,hashlib,random,heapq,copy
from pathlib import Path
from fractions import Fraction as F
from compiled_map_weighted_tree_v1 import Graph as New
from compiled_criticality_tree_v1 import Graph as Old
R=Path(__file__).resolve().parents[1];D=R/'experiments/map_weighted_primitive_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reference(fields,inc,initial,source,target,c,cost,budget,H):
 n=len(initial);p,q=c.numerator,c.denominator;dist={source:p*initial[source]};parent={};heap=[(dist[source]+H[source],source)];visited=set();settled=edges=0;pushes=1
 while heap:
  priority,u=heapq.heappop(heap)
  if u in visited or priority!=dist[u]+H[u]:continue
  visited.add(u);settled+=1
  if u==target:
   path=[];raw=initial[source];v=u
   while v!=source:
    a,slot=parent[v];path.append(slot);raw+=inc[slot];v=a
   path.reverse();return {'status':'COMMITTED' if raw<=budget else 'RETAIN_RAW_BUDGET','raw':raw,'objective_numerator':dist[u],'path_slots':tuple(path)},(settled,edges,pushes)
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   edges+=1;v=fields['dest_ranks'][slot]
   if v==source or v in visited:continue
   g=dist[u]+p*inc[slot]+(q-p)*cost.get(v,0)
   if v not in dist or g<dist[v]:dist[v]=g;parent[v]=(u,slot);heapq.heappush(heap,(g+H[v],v));pushes+=1
 return {'status':'UNREACHABLE'},(settled,edges,pushes)
def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261020);cases=0;failures=0;nonoptimal=0;retained=0
 for graph_index in range(200):
  n=rng.randrange(2,11);rows=[0];dest=[];inc=[]
  for u in range(n):
   for v in range(n):
    if u!=v and rng.random()<.32:dest.append(v);inc.append(rng.randrange(6))
   rows.append(len(dest))
  fields={'row_offsets':rows,'dest_ranks':dest};initial=[rng.randrange(4) for _ in range(n)];old=Old(fields,inc,initial);control=New(fields,inc,initial);weighted=New(fields,inc,initial)
  for _ in range(12):
   source,target=rng.sample(range(n),2);c=F(rng.randrange(9),8);cost={u:rng.randrange(17) for u in range(n)};budget=rng.randrange(18);zero=[0]*n;H=[rng.randrange(60) for _ in range(n)];a=old.tree(source);b=control.tree(source);x=a.expand(target,c,cost,budget);y=b.expand(target,c,cost,budget,zero,[1]*n);assert x==y and a.arrival==b.arrival and a.parents==b.parents and old.last_stats==control.last_stats;tree=weighted.tree(source);before=copy.deepcopy((tree.arrival,tree.parents));answer=tree.expand(target,c,cost,budget,H,[1]*n);ref,stats=reference(fields,inc,initial,source,target,c,cost,budget,H);assert answer['status']==ref['status'] and weighted.last_stats[:3]==stats
   for key in ['raw','objective_numerator','path_slots']:
    if key in ref:assert answer[key]==ref[key]
   if not answer['committed']:assert (tree.arrival,tree.parents)==before;failures+=1
   if answer['committed']:
    before=copy.deepcopy((tree.arrival,tree.parents));again=tree.expand(target,c,cost,budget,H,[1]*n);assert (tree.arrival,tree.parents)==before and again['raw']==answer['raw'];retained+=1
   if x['status']!='UNREACHABLE' and answer['status']!='UNREACHABLE':nonoptimal+=answer['objective_numerator']>x['objective_numerator']
   cases+=1
  old.close();control.close();weighted.close()
 fields={'row_offsets':[0,1,2,2],'dest_ranks':[1,2]};g=New(fields,[1,1],[0,0,0]);t=g.tree(0);before=copy.deepcopy((t.arrival,t.parents));bad=[lambda:t.expand(2,F(1),{},10,[0,0],[1,1,1]),lambda:t.expand(2,F(1),{},10,[0,-1,0],[1,1,1]),lambda:t.expand(2,F(1),{},10,[0,0,0],[1,0,1]),lambda:t.expand(2,F(1),{},10,[0,0,0],[1,1,0]),lambda:t.expand(2,F(1),{},10,[0,0,0],[1,2,1])]
 for fn in bad:
  try:fn()
  except ValueError:pass
  else:raise AssertionError('bad domain accepted')
  assert (t.arrival,t.parents)==before
 assert t.expand(2,F(1),{},10,[0,0,0],[1,1,1])['committed'];g.close();assert cases==2400 and nonoptimal>0
 files=[Path(__file__),R/'tools/compiled_map_weighted_tree_v1.py',R/'tools/soft_demand_cpp/map_weighted_criticality_v1.cpp',R/'tools/compiled_criticality_tree_v1.py',R/'build/map_weighted_criticality_v1_2026-10-20/receipt.json',R/'build/map_weighted_criticality_v1_2026-10-20/search.so'];(D/'verification.json').write_text(json.dumps({'status':'ALL2400_ARBITRARY_HEURISTIC_REFERENCE_AND_EXACT_H0_CONTROL_CASES_PASS','graphs':200,'cases':cases,'unchanged_failed_trees':failures,'retained_target_continuations':retained,'weighted_objective_worse_than_H0_cases':nonoptimal,'invalid_rejections':5,'bindings':{str(p):sha(p) for p in files},'scope':'Primitive random cyclic/zero-increment graphs with arbitrary inconsistentH, H0 full path/raw/objective/work parity, failed budget/domain purity. Weighted not optimal/native-equivalent, no actual MAP graph fixtures yet.'},indent=2)+'\n');print('MAP_WEIGHTED_CONTRACT_PASS',cases,nonoptimal)
if __name__=='__main__':main()
