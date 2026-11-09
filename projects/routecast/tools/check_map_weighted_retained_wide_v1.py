"""Independent multiseed retained-tree expansions and wide integer objectives."""
import random,heapq,json,copy,hashlib
from pathlib import Path
from fractions import Fraction as F
from compiled_map_weighted_tree_v1 import Graph as New
from compiled_criticality_tree_v1 import Graph as Old
R=Path(__file__).resolve().parents[1];D=R/'experiments/map_weighted_retained_wide_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reference(fields,inc,arrival,parents,source,target,c,cost,budget,H):
 p,q=c.numerator,c.denominator;dist={u:p*raw for u,raw in arrival.items()};heap=[(g+H[u],u) for u,g in dist.items()];heapq.heapify(heap);prev={};visited=set();stats=[0,0,len(heap)];seeds=set(arrival)
 while heap:
  priority,u=heapq.heappop(heap)
  if u in visited or priority!=dist[u]+H[u]:continue
  visited.add(u);stats[0]+=1
  if u==target:
   tail=[];raw=0
   while u not in seeds:
    parent,slot=prev[u];tail.append(slot);raw+=inc[slot];u=parent
   attach=u;raw+=arrival[u];prefix=[]
   while u!=source:parent,slot=parents[u];prefix.append(slot);u=parent
   return {'status':'COMMITTED' if raw<=budget else 'RETAIN_RAW_BUDGET','raw':raw,'objective_numerator':dist[target],'attach':attach,'path_slots':tuple(reversed(prefix))+tuple(reversed(tail))},tuple(stats)
  for slot in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
   stats[1]+=1;v=fields['dest_ranks'][slot]
   if v in seeds or v in visited:continue
   value=dist[u]+p*inc[slot]+(q-p)*cost.get(v,0)
   if v not in dist or value<dist[v]:dist[v]=value;prev[v]=(u,slot);heapq.heappush(heap,(value+H[v],v));stats[2]+=1
 return {'status':'UNREACHABLE'},tuple(stats)
def main():
 D.mkdir(exist_ok=False);rng=random.Random(76620261020);count=0;multiseed=0;failed=0
 for _ in range(80):
  n=rng.randrange(3,11);row=[0];dest=[];inc=[]
  for u in range(n):
   for v in range(n):
    if u!=v and rng.random()<.4:dest.append(v);inc.append(rng.randrange(8))
   row.append(len(dest))
  fields={'row_offsets':row,'dest_ranks':dest};initial=[rng.randrange(3) for _ in range(n)];a=Old(fields,inc,initial);b=New(fields,inc,initial);w=New(fields,inc,initial);source=rng.randrange(n);ta,tb,tw=a.tree(source),b.tree(source),w.tree(source)
  for j in range(12):
   target=rng.randrange(n);c=F(rng.randrange(8),7);cost={u:rng.randrange(11) for u in range(n)};budget=rng.randrange(25);H=[rng.randrange(80) for _ in range(n)];before=copy.deepcopy((tw.arrival,tw.parents));expect,stats=reference(fields,inc,tw.arrival,tw.parents,source,target,c,cost,budget,H);answer=tw.expand(target,c,cost,budget,H,[1]*n);assert w.last_stats[:3]==stats and answer['status']==expect['status']
   for key in ['raw','objective_numerator','attach','path_slots']:
    if key in expect:assert answer[key]==expect[key]
   if not answer['committed']:assert (tw.arrival,tw.parents)==before;failed+=1
   multiseed+=len(before[0])>1;x,y=ta.expand(target,c,cost,budget),tb.expand(target,c,cost,budget,[0]*n,[1]*n);assert x==y and a.last_stats==b.last_stats and (ta.arrival,ta.parents)==(tb.arrival,tb.parents);count+=1
  a.close();b.close();w.close()
 fields={'row_offsets':[0,2,3,3],'dest_ranks':[1,2,2]};inc=[1<<120,1<<121,1<<119];initial=[1<<119,0,0];old,new=Old(fields,inc,initial),New(fields,inc,initial);c=F(1<<62,(1<<63)-1);cost={0:1<<123,1:1<<124,2:1<<125};a,b=old.tree(0),new.tree(0);x=a.expand(2,c,cost,1<<127);y=b.expand(2,c,cost,1<<127,[0]*3,[1]*3);assert x==y and x['objective_numerator']>2**180 and old.last_stats==new.last_stats;wide_bits=x['objective_numerator'].bit_length();old.close();new.close();files=[Path(__file__),R/'tools/compiled_map_weighted_tree_v1.py',R/'build/map_weighted_criticality_v1_2026-10-20/search.so',R/'experiments/map_weighted_primitive_contract_v1_2026-10-20/verification.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL960_SEQUENTIAL_RETAINED_TREE_EXPANSIONS_AND_WIDE_H0_PARITY_PASS','queries':count,'multiseed_queries':multiseed,'failed_queries_tree_unchanged':failed,'wide_objective_bits':wide_bits,'bindings':{str(p):sha(p) for p in files},'scope':'Tiny graph primitive retained-tree/128raw/256score evidence. No native MAP real graph fixtures, generic routing semantics or quality/gain proof.'},indent=2)+'\n');print('RETAINED_WIDE_PASS',count,multiseed,wide_bits)
if __name__=='__main__':main()
