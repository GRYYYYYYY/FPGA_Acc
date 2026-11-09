"""Independent exact oracle and nonmutation checks for a two-pin tree gate."""
import copy,random
from fractions import Fraction
from criticality_objective_admission_v1 import prepare
class RC:
 def initial(self,u):return 0
 def increment(self,e):return [2,3,1,1][e]
f={'capacities':[1,1,1,1],'edge_ids':[10,11,12,13],'row_offsets':[0,2,3,4,4],'dest_ranks':[1,2,3,3]};slots={e:i for i,e in enumerate(f['edge_ids'])};qs=[dict(connection_id=0,net_id=7,source=0,sink=3)]
def record(path,delay):return [dict(qs[0],answer=dict(status='FOUND',physical_edge_ids=path,delay=delay),budget_integer=20,floor_integer=3)]
old=record([10,12],3);new=record([11,13],4);rng=random.Random(1480);relations=set()
for _ in range(1000):
 c=Fraction(rng.randrange(9),8);crit={0:dict(criticality_numerator=c.numerator,criticality_denominator=c.denominator)};cost={n:rng.randrange(21) for n in range(4)};ledger={0:1,1:1,3:1}
 if rng.randrange(2):ledger[2]=1
 frozen=copy.deepcopy((f,old,new,ledger,crit,cost));p=prepare(f,RC(),slots,qs,old,new,ledger,crit,cost)
 # Direct closed-form oracle: source excluded, one pin, exact union charge.
 before=c*3+(1-c)*(cost[1]+cost[3]);after=c*4+(1-c)*(cost[2]+cost[3]);delta=after-before
 overflow_delta=int(ledger.get(2,0)==1)
 assert (p['old_score'],p['candidate_score'],p['objective_delta'])==(before,after,delta)
 assert p['prospective_overflow_delta']==overflow_delta
 assert p['accepted']==(delta<=0 and overflow_delta<=0)
 assert frozen==(f,old,new,ledger,crit,cost);relations.add('worse' if delta>0 else 'better' if delta<0 else 'tie')
assert relations=={'worse','better','tie'}
print('PASS 1000 exact objective/overflow/nonmutation oracle cases')
# Shared-node congestion is charged once at maximum user criticality.
qs2=[qs[0],dict(connection_id=1,net_id=7,source=0,sink=1)]
a=old+[dict(qs2[1],answer=dict(status='FOUND',physical_edge_ids=[10],delay=2),budget_integer=20,floor_integer=2)]
b=new+[dict(qs2[1],answer=dict(status='FOUND',physical_edge_ids=[10],delay=2),budget_integer=20,floor_integer=2)]
crit={0:dict(criticality_numerator=1,criticality_denominator=4),1:dict(criticality_numerator=3,criticality_denominator=4)};cost={0:999,1:8,2:4,3:12};ledger={0:1,1:1,3:1}
p=prepare(f,RC(),slots,qs2,a,b,ledger,crit,cost)
assert p['old_score']==Fraction(3,4)+Fraction(3,2)+2+9
assert p['candidate_score']==1+Fraction(3,2)+2+3+9
assert not p['accepted'] and p['status']=='RETAIN_OBJECTIVE_INCREASE'
print('PASS shared-node maximum criticality/source exemption regression')
