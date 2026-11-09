"""Exhaustive Python message reference, full-table corrupted proof/overflow rejects."""
import random,itertools,json,hashlib
from array import array
from pathlib import Path
from compiled_exact_min_sum_v1 import Factor,Message,eliminate,verify_message,BINARY,MAX
R=Path(__file__).resolve().parents[1];D=R/'experiments/exact_min_sum_kernel_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reference(cards,var,factors):
 sep=sorted({n for f in factors for n in f.scope}-{var});costs=[];args=[]
 for rest in itertools.product(*(range(cards[n]) for n in sep)):
  a=dict(zip(sep,rest));options=[]
  for state in range(cards[var]):
   a[var]=state;score=0
   for f in factors:
    index=0
    for n in f.scope:index=index*cards[n]+a[n]
    score+=f.values[index]
   options.append(score)
  value=min(options);costs.append(value);args.append(options.index(value))
 return sep,costs,args
def reject(fn):
 try:fn()
 except (ValueError,MemoryError):return 1
 raise AssertionError('invalid input/proof accepted')
def main():
 D.mkdir(exist_ok=False);rng=random.Random(110220261020);cells=0;rejected=0
 for case in range(500):
  cards={n:rng.randrange(1,4) for n in range(rng.randrange(1,7))};var=rng.choice(list(cards));factors=[]
  for _ in range(rng.randrange(0,7)):
   scope=tuple(rng.sample(list(cards),rng.randrange(len(cards)+1)));length=1
   for n in scope:length*=cards[n]
   factors.append(Factor(scope,[rng.randrange(100)+(1<<58 if case%7==0 else 0) for i in range(length)]))
  before=[f.values.tobytes() for f in factors];sep,expected,arg=reference(cards,var,factors);m=eliminate(cards,var,factors);assert m.separator==tuple(sep) and list(m.factor.values)==expected and list(m.argmin)==arg;assert before==[f.values.tobytes() for f in factors];cells+=len(expected)
  bad=Message(var,sep,array('Q',m.factor.values),array('Q',m.argmin));bad.factor.values[0]^=1;rejected+=reject(lambda:verify_message(cards,var,factors,bad))
  bad=Message(var,sep,array('Q',m.factor.values),array('Q',m.argmin));bad.argmin[0]=cards[var];rejected+=reject(lambda:verify_message(cards,var,factors,bad))
 m=eliminate({0:2},0,[Factor((),[MAX])]);assert list(m.factor.values)==[MAX] and list(m.argmin)==[0]
 rejected+=reject(lambda:eliminate({0:2},0,[Factor((),[MAX]),Factor((),[1])]))
 rejected+=reject(lambda:eliminate({0:2},0,[Factor((0,),[1])]))
 rejected+=reject(lambda:eliminate({0:2},0,[Factor((1,),[0])]))
 rejected+=reject(lambda:eliminate({0:2,1:2},0,[Factor((1,),[1,2])],max_bytes=1))
 rejected+=reject(lambda:eliminate({0:MAX,1:2},0,[Factor((1,),[0,0])]))
 rejected+=reject(lambda:Factor((0,),[-1]))
 rejected+=reject(lambda:Factor((0,0),[0]))
 files=[Path(__file__),R/'tools/compiled_exact_min_sum_v1.py',R/'tools/soft_demand_cpp/exact_min_sum_v1.cpp',BINARY,R/'build/exact_min_sum_v1_2026-10-20/receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL500_EXHAUSTIVE_MESSAGES_AND_INDEPENDENT_ENUMERATOR_PROOFS_PASS','random_buckets':500,'message_cells':cells,'corrupt_or_invalid_rejections':rejected,'maximum_uint64_cost_valid':True,'bindings':{str(p):sha(p) for p in files},'scope':'Stateless bucket numeric proof only; full factor-model elimination/backtracking and real all72 optimization pending.'},indent=2)+'\n');print('EXACT_MIN_SUM_CONTRACT_PASS',cells,rejected)
if __name__=='__main__':main()
