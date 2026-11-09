"""Exhaustive original-count loss versus exact affine/nonlinear decomposition."""
import json,hashlib,random,itertools
from pathlib import Path
from collections import Counter
from aggregate_L1_affine_factorization_v1 import factorize,value
R=Path(__file__).resolve().parents[1];D=R/'experiments/aggregate_L1_affine_factorization_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);rng=random.Random(102320261020);assignments=0;kinds=Counter()
 for _ in range(400):
  domain=set(range(rng.randrange(1,10)));pools={n:[frozenset(x for x in domain if rng.random()<.5) for _ in range(rng.randrange(1,4))] for n in range(rng.randrange(1,6))};truth={n:rng.randrange(len(pools)+3) for n in domain};f=factorize(pools,truth,domain);assert f['constant']>=0 and all(min(c)>=0 for c in f['unary'].values());kinds.update(t['kind'] for t in f['node_terms'])
  for choices in itertools.product(*[range(len(pools[n])) for n in sorted(pools)]):
   selection=dict(zip(sorted(pools),choices));counts=Counter(x for n in pools for x in pools[n][selection[n]]);original=sum(abs(counts[x]-truth[x]) for x in domain);assert value(f,selection)==original;assignments+=1
  for t in f['node_terms']:
   lo,hi,target=t['fixed_count'],t['upper_count'],t['target'];assert (t['kind']=='nonlinear')==(lo<target<hi)
 p={0:[frozenset(),frozenset([0])],1:[frozenset(),frozenset([0])]};assert factorize(p,{0:1},{0})['node_terms'][0]['kind']=='nonlinear';assert not factorize(p,{0:0},{0})['nonlinear'];assert not factorize(p,{0:2},{0})['nonlinear'];assert value(factorize({0:[frozenset([0])]},{0:1},{0}),{0:0})==0
 files=[Path(__file__),R/'tools/aggregate_L1_affine_factorization_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL400_EXHAUSTIVE_ORIGINAL_AND_REDUCED_AGGREGATE_LOSSES_EQUAL','fixtures':400,'assignments':assignments,'node_kind_counts':dict(kinds),'bindings':{str(p):sha(p) for p in files},'scope':'Exact target-dependent loss representation only. No optimizer, rank/feasibility or label-free predictor claim.'},indent=2)+'\n');print('AFFINE_FACTOR_CONTRACT_PASS',assignments,dict(kinds))
if __name__=='__main__':main()
