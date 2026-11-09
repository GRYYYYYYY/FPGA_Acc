"""Independent exhaustive tiny full-ledger/cost reference; singleton parity."""
import json,hashlib,copy,itertools
from pathlib import Path
from fractions import Fraction as F
from shared_snapshot_group_plan_v1 import evaluate
from criticality_objective_admission_v1 import score
from criticality_net_occupancy_gate_v1 import plan
R=Path(__file__).resolve().parents[1];D=R/'experiments/shared_snapshot_group_contract_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False);sets=[{0},{1},{0,1}];cases=0;accepted=0
 for size in [1,2]:
  for patterns in itertools.product(sets,repeat=2*size):
   for caps in itertools.product([1,2],repeat=2):
    for external in itertools.product([0,1],repeat=2):
     old={i:{'owned':set(patterns[i]),'users':{n:F(i+1,3) for n in patterns[i]},'weighted_raw':F(i+1,7)} for i in range(size)};new={i:{'owned':set(patterns[size+i]),'users':{n:F(i+1,3) for n in patterns[size+i]},'weighted_raw':F(2-i,7)} for i in range(size)};ledger={n:external[n]+sum(n in t['owned'] for t in old.values()) for n in range(2)};base=[5,9];history={0:2};span={1:3};weight=2;snapshot=copy.deepcopy((ledger,old,new));actual=evaluate(caps,ledger,old,new,base,history,span,weight);future={n:external[n]+sum(n in t['owned'] for t in new.values()) for n in range(2)};pressure=sum(max(0,future[n]-caps[n])-max(0,ledger[n]-caps[n]) for n in range(2));cost={n:base[n]*(1+history.get(n,0))*(1+max(0,external[n]-caps[n]+1))+weight*span.get(n,0) for n in range(2)}
     def reference(trees):
      result=F(0)
      for t in trees.values():
       result+=t['weighted_raw']
       for n in range(2):
        if n in t['users']:result+=(1-t['users'][n])*cost[n]
      return result
     a,b=reference(old),reference(new);expected=pressure<=0 and b<=a;assert actual['old_score']==a and actual['candidate_score']==b and actual['overflow_delta']==pressure and actual['accepted']==expected;assert (ledger,old,new)==snapshot;assert actual['updates']==({n:future[n] for n in range(2) if future[n]!=ledger[n]} if expected else {});accepted+=expected;cases+=1
     if size==1:
      original=plan(caps,ledger,old[0]['owned'],new[0]['owned']);assert original['prospective_overflow_delta']==pressure
      fields={'dest_ranks':[0,1]};slots={0:0,1:1};cr={0:{'criticality_numerator':1,'criticality_denominator':3}}
      for trees,expected_score in [(old,a),(new,b)]:
       t=trees[0];records=[{'connection_id':0,'answer':{'physical_edge_ids':sorted(t['owned'])}}];delays={0:t['weighted_raw']*3};assert score(fields,slots,records,cr,cost,delays)==expected_score
 for invalid in ['underflow','net_domain','criticality']:
  a={0:{'owned':{0},'users':{0:F(1,2)},'weighted_raw':F(0)}};b=copy.deepcopy(a);ledger={0:1}
  if invalid=='underflow':ledger={}
  if invalid=='net_domain':b={1:b[0]}
  if invalid=='criticality':b[0]['users'][0]=F(2)
  try:evaluate([1],ledger,a,b,[1],{},{},0)
  except ValueError:pass
  else:raise AssertionError(invalid)
 files=[Path(__file__),R/'tools/shared_snapshot_group_plan_v1.py',R/'experiments/wbuart_sparse_pair_design_v1_2026-10-20/protocol.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL1440_TINY_GROUP_FULL_LEDGER_OBJECTIVES_PURITY_AND_REJECTIONS_PASS','cases':cases,'accepted':accepted,'invalid_rejections':3,'bindings':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Descriptor-level cost/occupancy contract, no physical path validator or real candidate pairing qualification.'},indent=2)+'\n');print('PASS_CASES',cases)
if __name__=='__main__':main()
