"""Full reference trainer vs sparse trainer, distinct spatial domains."""
import json,random
from pathlib import Path
from direct_rank_tree_reference_v1 import train as reference
from direct_rank_sparse_tree_v1 import train
from direct_rank_domain_v1 import training_objective
from check_direct_rank_split_sweep_v1 import make_domain
from exact_factor_elimination_v1 import sha

def main():
 rng=random.Random(20261020);nodes=0
 for trial in range(40):
  domains=[(str(c),make_domain(rng,6)) for c in range(2)];X=[[rng.randint(-2,3) for _ in range(2)] for _ in range(12)]
  def evaluate(points):return training_objective(domains,[points[:6],points[6:]])
  expected=reference(X,evaluate,depth=2,minleaf=2);actual=train(X,domains,depth=2,minleaf=2);assert actual==expected;nodes+=len(actual['nodes'])
 root=Path(__file__).resolve().parents[1];D=root/'experiments/direct_rank_sparse_tree_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),root/'tools/direct_rank_sparse_tree_v1.py',root/'tools/direct_rank_tree_reference_v1.py',root/'tools/direct_rank_split_sweep_v1.py',root/'experiments/direct_rank_split_sweep_contract_v1_2026-10-20/verification.json'];v={'status':'PASS_SPARSE_TREES_FULL_REFERENCE_EXACT','trees':40,'nodes':nodes,'bindings':{str(p):sha(p) for p in files},'scope':'Tiny depth2/minleaf2 two distinct spatial cases; no full real fit or speed claim.'};(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],40,nodes)
if __name__=='__main__':main()
