"""Independent full reconstruction after insertions; failed insertions are atomic."""
import pathlib,json,random,copy,hashlib
from collections import Counter,defaultdict
from partial_shared_tree_ledger_v1 import PartialSharedTreeLedger
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/partial_shared_tree_ledger_core_v2_2026-10-19'
def snapshot(x):return copy.deepcopy((x.state,x.nodes,x.parents,x.parent_uses,x.occupancy,x.wire))
def check(x):
 refs=defaultdict(Counter);parents=defaultdict(dict);uses=defaultdict(Counter)
 for cid,path in x.state.items():
  n=x.queries[cid]['net_id'];refs[n].update(v for v,_ in path)
  for (u,_),(v,s) in zip(path,path[1:]):
   if v in parents[n]:assert parents[n][v]==(u,s)
   parents[n][v]=(u,s);uses[n][v]+=1
 occ=Counter(v for group in refs.values() for v in group);wire=Counter({n:sum(x.length.get(v,0) for v in group) for n,group in refs.items()});assert dict(x.nodes)==dict(refs) and dict(x.parents)==dict(parents) and dict(x.parent_uses)==dict(uses) and x.occupancy==occ and x.wire==wire

def main():
 O.mkdir(exist_ok=False);rng=random.Random(191024);success=0;rejected=0
 for trial in range(250):
  q={cid:dict(connection_id=cid,net_id=cid//3,source=cid//3,sink=10+cid) for cid in range(6)};caps=[rng.randrange(1,3) for _ in range(18)];length={v:rng.randrange(5) for v in range(18)};ledger=PartialSharedTreeLedger({},q,caps,length)
  untouched=snapshot(ledger);assert ledger.outside(0,2)==0 and snapshot(ledger)==untouched
  for cid in rng.sample(list(q),6):
   net=q[cid]['net_id'];mid=rng.randrange(2,8);path=[(net,None),(mid,0),(q[cid]['sink'],1)];before=snapshot(ledger)
   try:ledger.insert(cid,path);success+=1
   except ValueError:assert snapshot(ledger)==before;rejected+=1
   check(ledger)
  if ledger.state:
   cid=next(iter(ledger.state));before=snapshot(ledger)
   try:ledger.insert(cid,ledger.state[cid])
   except ValueError:assert snapshot(ledger)==before;rejected+=1
   else:raise AssertionError('duplicate accepted')
 # Explicit same-NET prefix reused once; incompatible parent must not mutate.
 q={0:dict(net_id=0,source=0,sink=4),1:dict(net_id=0,source=0,sink=5)};x=PartialSharedTreeLedger({0:[(0,None),(2,1),(4,2)]},q,[1]*6,{2:7});before=snapshot(x)
 try:x.insert(1,[(0,None),(1,0),(2,1),(5,2)])
 except ValueError:assert snapshot(x)==before;rejected+=1
 else:raise AssertionError('conflicting parent accepted')
 x.insert(1,[(0,None),(2,1),(5,2)]);check(x);assert x.occupancy[2]==1 and x.nodes[0][2]==2 and x.wire[0]==7
 out=dict(status='PARTIAL_SHARED_TREE_INSERTION_RECONSTRUCTION_AND_ATOMIC_FAILURE_PASS',random_states=250,successful_inserts=success,rejected_atomic_inserts=rejected,shared_prefix_single_NET_charge=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__).resolve(),R/'tools/partial_shared_tree_ledger_v1.py',R/'tools/incremental_shared_tree_ledger_v1.py']},scope='Ledger constraints only, external physical edge/RC/native pin admission remains required.')
 (O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],success,rejected)
if __name__=='__main__':main()
