"""Inverse owners oracle and promotion/demotion within the same sorted round."""
import json,random,copy,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from live_overuse_eligibility_v1 import decide
from source_binding_v2 import closure
D=R/'experiments/live_overuse_eligibility_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261020);checks=0
 for _ in range(100):
  owned={n:set(rng.sample(range(12),rng.randrange(1,8))) for n in range(8)};inverse=defaultdict(set)
  for net,nodes in owned.items():
   for node in nodes:inverse[node].add(net)
  caps=[rng.randrange(1,5) for _ in range(12)];ledger=Counter({n:len(v) for n,v in inverse.items()});saved=copy.deepcopy((owned,ledger,caps))
  for mask in range(256):
   dirty={n for n in range(8) if mask>>n&1}
   for net,nodes in owned.items():
    expected_nodes=sorted(node for node,owners in inverse.items() if net in owners and len(owners)>caps[node]);v=decide(net,dirty,nodes,ledger,caps);assert v==dict(eligible=net in dirty or bool(expected_nodes),endpoint_dirty=net in dirty,overused_nodes=expected_nodes);checks+=1
  assert (owned,ledger,caps)==saved
 # A moves pressure from node0 to node1; old overflow1 -> new overflow1.
 owned={0:{0},1:{0},2:{1}};ledger=Counter(node for nodes in owned.values() for node in nodes);caps=[1,1];epochs={0:2,1:7,2:9};saved_epoch=epochs[1];before=copy.deepcopy((owned,ledger,epochs));round_start=[n for n in owned if decide(n,set(),owned[n],ledger,caps)['eligible']];assert round_start==[0,1]
 assert decide(0,{0},owned[0],ledger,caps)['eligible'];owned[0]={1};ledger[0]-=1;ledger[1]+=1;epochs[0]+=1
 assert not decide(1,{0},owned[1],ledger,caps)['eligible'];assert epochs[1]==saved_epoch
 assert decide(2,{0},owned[2],ledger,caps)['eligible'] and 2 not in round_start
 assert sum(max(0,v-caps[n]) for n,v in ledger.items())==1
 # No cache: returning a clean result does not suppress a future dirty result.
 assert decide(1,{1},owned[1],ledger,caps)['eligible'];assert not decide(1,set(),owned[1],ledger,caps)['eligible']
 rejected=0
 for net,nodes,counts,capacity in [(-1,{0},{0:1},[1]),(True,{0},{0:1},[1]),(0,{-1},{0:1},[1]),(0,{0},{0:0},[1]),(0,{0},{0:True},[1]),(0,{0},{0:1},[0])]:
  try:decide(net,set(),nodes,counts,capacity)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid domain accepted')
 (D/'verification.json').write_text(json.dumps(dict(status='LIVE_OWNER_INVERSE_ORACLE_AND_WITHIN_ROUND_PROMOTION_DEMOTION_PASS',predicate_checks=checks,invalid_domains_rejected=rejected,round_start_vs_live_difference_exercised=True,input_mutations_absent=True,bindings=closure([Path(__file__)]),scope='Pure predicate only. Full producer skip/epoch/budget/timing audits still required; no native force-timing equivalence or quality claim.'),indent=2)+'\n');print('PASS',checks,rejected)
if __name__=='__main__':main()
