"""Meaningful immutable-adapter parity and lifetime tests on existing exact kernel."""
from pathlib import Path
from fractions import Fraction
import random,json,hashlib
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from compiled_criticality_tree_v2 import Graph,FrozenPrices,BINARY
R=Path(__file__).resolve().parents[1]
def main():
 O=R/'experiments/frozen_criticality_price_adapter_contract_v1_2026-10-19';O.mkdir(exist_ok=False);rng=random.Random(20261019);calls=0;rejections=0
 for trial in range(40):
  n=3+rng.randrange(15);rows=[0];dest=[];inc=[]
  for u in range(n):
   for v in range(n):
    if rng.random()<.16:dest.append(v);inc.append(rng.randrange(9)+(2**90 if trial%7==0 else 0))
   rows.append(len(dest))
  fields={'row_offsets':rows,'dest_ranks':dest};initial=[0]*n;original=[rng.randrange(9)+(2**95 if trial%7==0 else 0) for _ in range(n)];saved=tuple(original);frozen=FrozenPrices(original);original[0]+=1;assert frozen.values==saved;g=Graph(fields,inc,initial);r=Reference(fields,inc,initial)
  try:
   for source in [0,n-1]:
    a=g.tree(source);b=r.tree(source)
    for _ in range(30):
     target=rng.randrange(n);criticality=Fraction(rng.randrange(5),4);budget=2**120 if rng.randrange(2) else rng.randrange(15);before=dict(a.parents),dict(a.arrival);x=a.expand(target,criticality,frozen,budget);y=b.expand(target,criticality,dict(enumerate(saved)),budget);assert x==y and a.parents==b.parents and a.arrival==b.arrival
     if not x['committed']:assert (a.parents,a.arrival)==before;rejections+=1
     calls+=1
   caught=False
   try:g.tree(0).expand(0,Fraction(1),FrozenPrices([0]*(n+1)),0)
   except ValueError:caught=True
   assert caught
  finally:g.close()
  caught=False
  try:a.expand(0,Fraction(1),frozen,0)
  except RuntimeError:caught=True
  assert caught
  try:frozen.values=(0,)
  except AttributeError:pass
  else:raise AssertionError('mutable snapshot')
 for values in [[],[-1],[2**128],[True]]:
  try:FrozenPrices(values)
  except ValueError:pass
  else:raise AssertionError('invalid price accepted')
 files=[Path(__file__).resolve(),R/'tools/compiled_criticality_tree_v2.py',R/'tools/compiled_criticality_tree_v1.py',BINARY,R/'tools/criticality_shared_tree_sparse_reference_v3.py'];(O/'verification.json').write_text(json.dumps({'status':'FROZEN_PRICE_ADAPTER_REFERENCE_PARITY_IMMUTABILITY_DOMAIN_AND_LIFETIME_PASS','graphs':40,'expansions':calls,'atomic_rejections':rejections,'bindings':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Adapter-only random/wide parity; same kernel. Real full-graph41-call cost and parity pending.'},indent=2)+'\n');print('FROZEN_ADAPTER_PASS',calls,'expansions',rejections,'atomic rejections')
if __name__=='__main__':main()
