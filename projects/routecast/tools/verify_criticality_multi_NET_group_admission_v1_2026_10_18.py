"""Swap escape and independent exhaustive small resource-owner group oracle."""
import copy,json,random,hashlib
from pathlib import Path
from fractions import Fraction
from collections import Counter
from criticality_multi_NET_group_admission_v1 import prepare
from criticality_objective_admission_v1 import prepare as single
class RC:
 def __init__(self,weights):self.weights=weights
 def initial(self,node):return 0
 def increment(self,slot):return self.weights[slot]
def fixture(n,resources,caps,weights):
 arcs=[]
 for net in range(n):
  for j in range(resources):arcs.append((net,2*n+j,weights[net,j]))
 for j in range(resources):
  for net in range(n):arcs.append((2*n+j,n+net,1))
 arcs.sort();rows=[0];dest=[];ws=[];ids={}
 for u in range(2*n+resources):
  for a,b,w in arcs:
   if a==u:ids[a,b]=len(dest);dest.append(b);ws.append(w)
  rows.append(len(dest))
 f=dict(capacities=[100]*(2*n)+caps,row_offsets=rows,dest_ranks=dest,edge_ids=list(range(len(dest))));q={i:[dict(connection_id=i,net_id=i,source=i,sink=n+i)] for i in range(n)}
 def records(choice):
  out={}
  for i,j in enumerate(choice):
   path=[ids[i,2*n+j],ids[2*n+j,n+i]];out[i]=[dict(q[i][0],answer=dict(status='FOUND',physical_edge_ids=path,delay=weights[i,j]+1),budget_integer=10)]
  return out
 return f,RC(ws),{i:i for i in range(len(dest))},q,records

def main():
 rng=random.Random(76221);checks=0
 for trial in range(500):
  n=rng.randrange(2,5);resources=rng.randrange(2,5);caps=[rng.randrange(1,4) for _ in range(resources)];weights={(i,j):rng.randrange(1,8) for i in range(n) for j in range(resources)};f,rc,slots,q,records=fixture(n,resources,caps,weights);oldchoice=[rng.randrange(resources) for _ in range(n)];newchoice=[rng.randrange(resources) for _ in range(n)];old=records(oldchoice);new=records(newchoice);ledger=Counter({i:1 for i in range(2*n)});ledger.update(2*n+j for j in oldchoice);critical={i:dict(criticality_numerator=rng.randrange(5),criticality_denominator=4) for i in range(n)};prices={i:rng.randrange(7) for i in range(2*n+resources)};epoch={i:7 for i in range(n)};snapshot=copy.deepcopy((old,new,dict(ledger),epoch));plan=prepare(f,rc,slots,q,old,new,ledger,critical,prices,epoch,epoch)
  final=Counter({i:1 for i in range(2*n)});final.update(2*n+j for j in newchoice);delta=sum(max(0,final.get(i,0)-c)-max(0,ledger.get(i,0)-c) for i,c in enumerate(f['capacities']));before=after=Fraction(0)
  for i in range(n):
   c=Fraction(critical[i]['criticality_numerator'],4);before+=c*(weights[i,oldchoice[i]]+1)+(1-c)*(prices[2*n+oldchoice[i]]+prices[n+i]);after+=c*(weights[i,newchoice[i]]+1)+(1-c)*(prices[2*n+newchoice[i]]+prices[n+i])
  assert plan['prospective_overflow_delta']==delta and plan['objective_delta']==after-before and plan['accepted']==(delta<=0 and after<=before);assert snapshot==(old,new,dict(ledger),epoch);checks+=1
 # Two legally occupied resources: either single swap raises overflow, atomic swap does not.
 f,rc,slots,q,records=fixture(2,2,[1,1],{(0,0):2,(0,1):1,(1,0):1,(1,1):2});old=records([0,1]);new=records([1,0]);ledger=Counter({i:1 for i in range(6)});crit={i:dict(criticality_numerator=1,criticality_denominator=2) for i in range(2)};prices={i:0 for i in range(6)};epochs={0:0,1:0};one=[single(f,rc,slots,q[i],old[i],new[i],ledger,crit,prices) for i in range(2)];assert all(not x['accepted'] and x['prospective_overflow_delta']==1 for x in one);both=prepare(f,rc,slots,q,old,new,ledger,crit,prices,epochs,epochs);assert both['accepted'] and both['prospective_overflow_delta']==0 and both['objective_delta']==-1
 rejected=[]
 for name in ['stale_epoch','missing_NET','changed_budget','invalid_endpoint']:
  candidate=copy.deepcopy(new);expected=epochs.copy()
  if name=='stale_epoch':expected[1]=1
  elif name=='missing_NET':candidate.pop(1)
  elif name=='changed_budget':candidate[1][0]['budget_integer']=11
  else:candidate[1][0]['sink']=2
  try:prepare(f,rc,slots,q,old,candidate,ledger,crit,prices,epochs,expected)
  except ValueError:rejected.append(name)
  else:raise AssertionError(name)
 r=Path(__file__).resolve().parents[1];o=r/'experiments/multi_NET_group_admission_core_v1_2026-10-18';o.mkdir();paths=[Path(__file__).resolve(),r/'tools/criticality_multi_NET_group_admission_v1.py'];v=dict(status='pure_group_preparation_core_and_independent_small_graph_oracle_pass',independent_random_graphs=checks,read_only_input_snapshots_unchanged=True,single_NET_swap_both_rejected=True,group_swap_final_overflow_zero_objective_decreases=True,rejected_corruptions=rejected,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='New transaction granularity prototype only. No shared-state atomic publisher, joint search, native-equivalence, real graph or forecast gain; existing single-NET implementation unchanged.');(o/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],checks,rejected)
if __name__=='__main__':main()
