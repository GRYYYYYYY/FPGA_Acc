"""Quadratic graph reference and full-ledger proof checks for nonedge additivity."""
import json,hashlib,random,itertools
from pathlib import Path
from collections import Counter
from NET_candidate_interactions_v1 import interactions
R=Path(__file__).resolve().parents[1];D=R/'experiments/NET_candidate_interactions_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);rng=random.Random(84220261020);checks=0
 for _ in range(300):
  domain=set(range(rng.randrange(1,10)));pools={n:[frozenset(x for x in domain if rng.random()<.45) for _ in range(rng.randrange(1,4))] for n in range(rng.randrange(1,7))};g=interactions(pools);var={n:{r for r in domain if any(r in c for c in cs) and not all(r in c for c in cs)} for n,cs in pools.items()};expected=[(a,b,sorted(var[a]&var[b])) for a,b in itertools.combinations(sorted(pools),2) if var[a]&var[b]];assert expected==g['pairs'] and var==g['variable'];selected={n:rng.randrange(len(cs)) for n,cs in pools.items()};truth={n:rng.randrange(3) for n in domain}
  def cost(s):
   counts=Counter(r for n in s for r in pools[n][s[n]]);return sum(abs(counts[r]-truth[r]) for r in domain)
  baseline=cost(selected)
  for a,b in itertools.combinations(sorted(pools),2):
   if var[a]&var[b]:continue
   for ia,ib in itertools.product(range(len(pools[a])),range(len(pools[b]))):
    x=dict(selected);x[a]=ia;y=dict(selected);y[b]=ib;z=dict(selected);z[a]=ia;z[b]=ib;assert cost(z)-baseline==cost(x)+cost(y)-2*baseline;checks+=1
  assert sorted(n for c in g['components'] for n in c)==sorted(pools)
 files=[Path(__file__),R/'tools/NET_candidate_interactions_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL300_QUADRATIC_INTERACTION_GRAPHS_AND_NONEDGE_AGGREGATE_ADDITIVITY_CHECKS_PASS','fixtures':300,'nonedge_joint_choices':checks,'bindings':{str(p):sha(p) for p in files},'scope':'Graph determines possible coupling only, not strict improvements, learning signal or joint feasibility.'},indent=2)+'\n');print('INTERACTION_CONTRACT_PASS',checks)
if __name__=='__main__':main()
