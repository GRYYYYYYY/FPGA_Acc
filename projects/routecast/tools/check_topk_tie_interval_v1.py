import json,random,itertools
from pathlib import Path
from topk_tie_interval_v1 import interval
from exact_factor_elimination_v1 import sha

def main():
 rng=random.Random(20261020);subsets=0
 for trial in range(500):
  n=rng.randint(1,9);p={i:rng.randrange(3) for i in range(n)};t={i:rng.randrange(3) for i in range(n)};k=rng.randint(1,n);target=set(sorted(t,key=lambda i:(-t[i],i))[:k]);best=sorted(p.values(),reverse=True)[:k];hits=[]
  for chosen in itertools.combinations(range(n),k):
   if sorted((p[i] for i in chosen),reverse=True)==best:hits.append(len(target.intersection(chosen)));subsets+=1
  v=interval(p,t,k);assert min(hits)==v['minimum_hits'] and max(hits)==v['maximum_hits'] and v['minimum_hits']<=v['actual_ID_hits']<=v['maximum_hits']
 R=Path(__file__).resolve().parents[1];D=R/'experiments/topk_tie_interval_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/topk_tie_interval_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'PASS_EXHAUSTIVE_TOPK_SUBSET_INTERVALS','trials':500,'admissible_subsets':subsets,'bindings':{str(p):sha(p) for p in files}},indent=2)+'\n');print('TOPK_TIE_INTERVAL_PASS',subsets)
if __name__=='__main__':main()
