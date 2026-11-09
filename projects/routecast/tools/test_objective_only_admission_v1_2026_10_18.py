"""Independent arithmetic oracle on positive/zero/negative overflow transitions."""
import pathlib,sys,json,hashlib,copy
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from criticality_objective_only_admission_v1 import prepare
from criticality_objective_admission_v1 import prepare as original
class RC:
 def initial(self, node):return 0
 def increment(self, edge):return 1

def main():
 fields=dict(capacities=[1]*4,edge_ids=[0,1,2,3],row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,3]);slots={x:x for x in range(4)};q=dict(connection_id=0,net_id=0,source=0,sink=3);old=[dict(q,answer=dict(status='FOUND',physical_edge_ids=[0,2],delay=2),budget_integer=2)];new=[dict(q,answer=dict(status='FOUND',physical_edge_ids=[1,3],delay=2),budget_integer=2)];count=positive=0
 for a in [1,2]:
  for b in [0,1,2]:
   for numerator in [0,1,2]:
    c=Fraction(numerator,2);criticalities={0:dict(criticality_numerator=numerator,criticality_denominator=2)}
    for left in range(6):
     for right in range(6):
      ledger={0:1,1:a,2:b,3:1};prices={1:left,2:right};snapshot=copy.deepcopy((old,new,ledger,criticalities,prices));p=prepare(fields,RC(),slots,[q],old,new,ledger,criticalities,prices);base=original(fields,RC(),slots,[q],old,new,ledger,criticalities,prices);after=dict(ledger);after[1]-=1;after[2]+=1;overflow=lambda x:sum(max(0,v-1) for v in x.values());delta=overflow(after)-overflow(ledger);objective_delta=(1-c)*(right-left);accept=objective_delta<=0
      assert p['prospective_overflow_delta']==delta and p['objective_delta']==objective_delta and p['accepted']==accept;assert base['accepted']==(accept and delta<=0)
      if accept:assert p['updates']=={1:a-1,2:b+1}
      else:assert not p['updates']
      assert (old,new,ledger,criticalities,prices)==snapshot
      positive+=bool(accept and delta>0);count+=1
 # Budget violations remain hard failures of the separate policy.
 invalid=copy.deepcopy(new);invalid[0]['budget_integer']=1
 try:prepare(fields,RC(),slots,[q],old,invalid,{0:1,1:1,3:1},{0:dict(criticality_numerator=1,criticality_denominator=2)},{1:5,2:1})
 except ValueError:pass
 else:raise AssertionError('budget violation admitted')
 out=R/'experiments/objective_only_admission_contract_v1_2026-10-18';out.mkdir();paths=[pathlib.Path(__file__).resolve(),R/'tools/criticality_objective_only_admission_v1.py'];(out/'verification.json').write_text(json.dumps(dict(status='independent_transition_and_objective_oracles_pass',cases=count,positive_overflow_objective_admitted=positive,all_inputs_unchanged=True,budget_failure_rejected=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Pure singleNET plan on finite fixture transitions; no epoch publisher, real graph quality or native convergence claim.'),indent=2)+'\n');print(count,positive,flush=True)
if __name__=='__main__':main()
