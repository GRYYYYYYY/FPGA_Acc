"""Full small model exhaustive optimum, packed dependency proof and forged proof rejects."""
import json,random,itertools,tempfile,shutil,hashlib
from pathlib import Path
from math import prod
from array import array
from compiled_exact_min_sum_v1 import Factor,MAX
from exact_factor_elimination_v1 import solve,evaluate,verify_certificate,sha
from symbolic_NET_elimination_v1 import plan
R=Path(__file__).resolve().parents[1];D=R/'experiments/exact_factor_elimination_contract_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);rng=random.Random(111220261020);models=0;assignments=0;messages=0
 for _ in range(250):
  cards={n:rng.randrange(1,4) for n in range(rng.randrange(1,7))};factors=[]
  for j in range(rng.randrange(0,8)):
   scope=tuple(rng.sample(list(cards),rng.randrange(len(cards)+1)));factors.append(Factor(scope,[rng.randrange(31) for i in range(prod(cards[n] for n in scope))]))
  constant=rng.randrange(20);order=[s['NET'] for s in plan(cards,[f.scope for f in factors])['steps']];answer=solve(cards,factors,order,constant);values=[evaluate(cards,factors,dict(zip(cards,choice)),constant) for choice in itertools.product(*(range(cards[n]) for n in cards))];assert answer['objective']==min(values);assignments+=len(values);models+=1;messages+=answer['messages']
 cards={0:2,1:2,2:1};factors=[Factor((0,1),[0,0,0,0]),Factor((2,),[7]),Factor((),[3])];directory=D/'packed_fixture';answer=solve(cards,factors,[0,1],5,directory);verified=verify_certificate(directory);assert verified['objective']==answer['objective']==15 and verified['selected']=={0:0,1:0,2:0}
 rejects=0
 with tempfile.TemporaryDirectory(prefix='routecast_minsum_forged_') as tmp:
  for role in ['table','argmin']:
   forged=Path(tmp)/role;shutil.copytree(directory,forged);m=json.loads((forged/'certificate.json').read_text());desc=m['steps'][0][role];bank=forged/desc['file'];raw=bytearray(bank.read_bytes());a=array('Q');a.frombytes(raw[desc['offset_bytes']:desc['offset_bytes']+desc['count']*8]);a[0]+=1;raw[desc['offset_bytes']:desc['offset_bytes']+desc['count']*8]=a.tobytes();bank.write_bytes(raw);desc['sha256']=hashlib.sha256(memoryview(a)).hexdigest();m['files'][desc['file']]['sha256']=sha(bank);(forged/'certificate.json').write_text(json.dumps(m))
   try:verify_certificate(forged)
   except ValueError:rejects+=1
   else:raise AssertionError('forged recurrence proof admitted')
 try:solve({0:1},[Factor((),[MAX]),Factor((),[1])],[])
 except ValueError:rejects+=1
 else:raise AssertionError('constant overflow admitted')
 try:solve({0:2,1:2},[],[0])
 except ValueError:rejects+=1
 else:raise AssertionError('partial variable elimination admitted')
 files=[Path(__file__),R/'tools/exact_factor_elimination_v1.py',R/'tools/compiled_exact_min_sum_v1.py',R/'experiments/exact_min_sum_kernel_contract_v1_2026-10-20/verification.json',directory/'certificate.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL250_EXHAUSTIVE_GLOBAL_MINIMA_AND_PACKED_CERTIFICATE_FORGERY_CHECKS_PASS','models':models,'assignments':assignments,'message_recurrences_checked':messages,'invalid_or_forged_rejections':rejects,'bindings':{str(p):sha(p) for p in files},'scope':'Generic exact integer model inference/backtracking; all72 real objective identities/rank diagnostics still pending.'},indent=2)+'\n');print('FULL_EXACT_ELIMINATION_PASS',models,assignments,messages,rejects)
if __name__=='__main__':main()
