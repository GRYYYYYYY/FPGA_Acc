"""Independent full-ledger recomputation of every bounded coordinate decision."""
import json,hashlib,random,itertools
from pathlib import Path
from collections import Counter
from coordinate_NET_aggregate_L1_v1 import select
R=Path(__file__).resolve().parents[1];D=R/'experiments/coordinate_NET_aggregate_L1_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reference(pools,initial,truth,domain,limit):
 selected=dict(initial);moves=[];rounds=[]
 def rebuild(s):return Counter(n for net in pools for n in pools[net][s[net]])
 def loss(s):
  counts=rebuild(s);return sum(abs(counts[n]-truth.get(n,0)) for n in domain)
 initial_loss=loss(selected)
 for sweep in range(limit):
  changed=0
  for net in sorted(pools):
   old=selected[net];before=loss(selected);best=old;bestscore=before
   for index in range(len(pools[net])):
    proposal=dict(selected);proposal[net]=index;score=loss(proposal)
    if score<bestscore:best,bestscore=index,score
   if best!=old:moves.append({'sweep':sweep,'net_id':net,'old_choice':old,'new_choice':best,'delta':bestscore-before,'before_L1':before,'after_L1':bestscore});selected[net]=best;changed+=1
  rounds.append({'sweep':sweep,'moves':changed,'L1':loss(selected)})
  if not changed:break
 return {'status':'ONE_NET_LOCAL_OPTIMUM' if not rounds[-1]['moves'] else 'SWEEP_LIMIT_NOT_OPTIMALITY_PROOF','selected':selected,'counts':dict(rebuild(selected)),'initial_L1':initial_loss,'final_L1':loss(selected),'moves':moves,'sweeps':rounds}
def main():
 D.mkdir(exist_ok=False);rng=random.Random(83220261020);moves=0
 for _ in range(400):
  domain=set(range(rng.randrange(1,12)));pools={n:[frozenset(x for x in domain if rng.random()<.4) for _ in range(rng.randrange(1,5))] for n in range(rng.randrange(1,9))};initial={n:rng.randrange(len(c)) for n,c in pools.items()};truth={n:rng.randrange(4) for n in domain};limit=rng.randrange(1,6);a=select(pools,initial,truth,domain,limit);b=reference(pools,initial,truth,domain,limit);assert a==b;moves+=len(a['moves'])
  for m in a['moves']:assert m['delta']<0 and m['after_L1']<m['before_L1']
 pools={0:[frozenset([0]),frozenset([2])],1:[frozenset([2]),frozenset([1])],2:[frozenset([0])]};initial={0:0,1:0,2:0};truth={0:1,1:1,2:1};answer=select(pools,initial,truth,{0,1,2});assert answer['status']=='ONE_NET_LOCAL_OPTIMUM' and answer['final_L1']==2
 minimum=min(sum(abs(sum(n in pools[net][choice] for net,choice in enumerate(choices))-1) for n in range(3)) for choices in itertools.product(*[range(len(pools[n])) for n in range(3)]));assert minimum==0
 files=[Path(__file__),R/'tools/coordinate_NET_aggregate_L1_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL400_COORDINATE_TRACES_MATCH_FULL_REBUILD_REFERENCE_LOCAL_NOT_GLOBAL_TRAP_VERIFIED','fixtures':400,'strict_moves_verified':moves,'known_local_trap_L1':2,'same_pool_global_L1':0,'bindings':{str(p):sha(p) for p in files},'scope':'Bounded diagnostic decision/update exactness only, not global optimum or deployable use of truth.'},indent=2)+'\n');print('COORDINATE_CONTRACT_PASS',moves,'local2 global0')
if __name__=='__main__':main()
