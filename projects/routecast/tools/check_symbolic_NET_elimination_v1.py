"""Independent factor-bucket elimination and known graph width fixtures."""
import random,json,hashlib,itertools,math
from pathlib import Path
from symbolic_NET_elimination_v1 import plan
R=Path(__file__).resolve().parents[1];D=R/'experiments/symbolic_NET_elimination_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);rng=random.Random(92420261020);steps=0
 for _ in range(300):
  n=rng.randrange(1,13);cards={i:rng.randrange(1,4) for i in range(n)};scopes=[set(rng.sample(range(n),rng.randrange(1,min(n,4)+1))) for j in range(rng.randrange(1,18))];answer=plan(cards,scopes);active={v for v in cards if cards[v]>1};factors=[s&active for s in scopes]
  for row in answer['steps']:
   scores={};bags={}
   for v in active:
    bag={v}|set().union(*(s for s in factors if v in s));neighbors=bag-{v};edges={tuple(sorted(e)) for s in factors for e in itertools.combinations(s,2)};missing=[list(e) for e in itertools.combinations(sorted(neighbors),2) if e not in edges];scores[v]=[len(missing),math.prod(cards[x] for x in bag),len(neighbors),v];bags[v]=(bag,missing)
   chosen=min(active,key=lambda v:scores[v]);assert chosen==row['NET'] and scores[chosen]==row['minfill_score'];bag,missing=bags[chosen];assert row['neighbors']==sorted(bag-{chosen}) and row['fill_edges']==missing;assert row['separator_states']==math.prod(cards[v] for v in bag-{chosen});factors=[s for s in factors if chosen not in s]+[bag-{chosen}];active.remove(chosen);steps+=1
  assert not active and len(answer['fixed_NETs'])+len(answer['steps'])==n
 chain=plan({i:2 for i in range(7)},[{i,i+1} for i in range(6)]);assert chain['induced_width']==1 and chain['largest_bag_states']==4
 star=plan({i:3 for i in range(7)},[{0,i} for i in range(1,7)]);assert star['induced_width']==1 and star['largest_bag_states']==9
 clique=plan({i:2 for i in range(6)},[set(range(6))]);assert clique['induced_width']==5 and clique['largest_bag_states']==64
 files=[Path(__file__),R/'tools/symbolic_NET_elimination_v1.py'];(D/'verification.json').write_text(json.dumps({'status':'ALL300_SYMBOLIC_BUCKET_PLANS_AND_CHAIN_STAR_CLIQUE_FIXTURES_PASS','fixtures':300,'eliminations':steps,'bindings':{str(p):sha(p) for p in files},'scope':'Structural plan correctness; greedy min-fill is not optimal treewidth and no numerical inference/forecast executed.'},indent=2)+'\n');print('SYMBOLIC_ELIMINATION_PASS',steps)
if __name__=='__main__':main()
