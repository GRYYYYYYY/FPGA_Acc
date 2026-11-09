"""Prepared numeric buffers versus frozen scalar compiled tree, retained sequential calls."""
import random,struct,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from prepared_map_priority_v1 import Priority
from compiled_prepared_map_tree_v1 import Graph as New
from compiled_map_weighted_tree_v1 import Graph as Old
from check_map_materialize_v2 import ref
R=Path(__file__).resolve().parents[1];D=R/'experiments/prepared_map_tree_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);rng=random.Random(675520261020);count=0
 for _ in range(120):
  n=rng.randrange(3,14);row=[0];dest=[];inc=[]
  for u in range(n):
   for v in range(n):
    if u!=v and rng.random()<.35:dest.append(v);inc.append(rng.randrange(10))
   row.append(len(dest))
  fields={'row_offsets':row,'dest_ranks':dest};initial=[rng.randrange(4) for _ in range(n)];old,new=Old(fields,inc,initial),New(fields,inc,initial);src=rng.randrange(n);a,b=old.tree(src),new.tree(src)
  for j in range(10):
   target=rng.randrange(n);c=F(rng.randrange(5),4);budget=rng.randrange(35);cost={i:rng.randrange(30) for i in range(n)};data=b''.join(struct.pack('<ff',rng.random()*1e-9,rng.random()*1e-9) for i in range(n));bits=struct.pack('>f',float(c)).hex();priority=Priority.materialize(data,[1]*n,[0]*n,bits,10**18,c.denominator) if j%2 else Priority([1]*n);H=ref(data,[1]*n,[0]*n,bits,10**18,c.denominator) if j%2 else (0,)*n;assert priority.maximum==max(H);assert tuple(priority.storage[2*i]+(priority.storage[2*i+1]<<64) for i in range(n))==H;x=a.expand(target,c,cost,budget,H,[1]*n);y=b.expand(target,c,cost,budget,priority);assert x==y and old.last_stats==new.last_stats and (a.arrival,a.parents)==(b.arrival,b.parents);count+=1
  old.close();new.close()
 files=[Path(__file__),R/'tools/prepared_map_priority_v1.py',R/'tools/compiled_prepared_map_tree_v1.py',R/'tools/soft_demand_cpp/map_priority_materialize_v3.cpp',R/'build/map_priority_materialize_v3_2026-10-20/materialize.so'];(D/'verification.json').write_text(json.dumps({'status':'ALL1200_SEQUENTIAL_PREPARED_H0_MAP_EXACT_SCALAR_TREE_PATH_OBJECTIVE_WORK_PARITY_PASS','queries':count,'bindings':{str(p):sha(p) for p in files},'scope':'Prepared buffer numeric/tree integration qualification; full real-model trajectory parity pending.'},indent=2)+'\n');print('PREPARED_TREE_PASS',count)
if __name__=='__main__':main()
