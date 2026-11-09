"""Compare independent affected-case rebuild against qualified sparse scan."""
import json,random
from pathlib import Path
from direct_rank_split_sweep_v1 import scan
from direct_rank_rebuild_scan_v1 import scan as rebuild
from check_direct_rank_split_sweep_v1 import make_domain
from exact_factor_elimination_v1 import sha

def main():
 rng=random.Random(20261020);count=0
 for trial in range(80):
  domains=[(str(i),make_domain(rng,rng.randint(3,9))) for i in range(rng.randint(1,3))];fields=[[rng.randrange(2) for _ in d.ids] for _,d in domains];n=sum(len(d.ids) for _,d in domains);X=[[rng.randrange(4) for _ in range(3)] for _ in range(n)];members=rng.sample(range(n),rng.randint(1,n));minleaf=rng.randint(1,3);a=scan(X,domains,fields,members,minleaf);b=rebuild(X,domains,fields,members,minleaf);assert all(a[k]==v for k,v in b.items());count+=b['candidates']
 R=Path(__file__).resolve().parents[1];D=R/'experiments/direct_rank_rebuild_scan_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/direct_rank_rebuild_scan_v1.py',R/'tools/direct_rank_split_sweep_v1.py',R/'experiments/direct_rank_split_sweep_contract_v1_2026-10-20/verification.json'];(D/'verification.json').write_text(json.dumps({'status':'PASS_INDEPENDENT_REBUILD_SCAN','trials':80,'candidates':count,'bindings':{str(p):sha(p) for p in files},'scope':'Independent complete affected-case rank scoring; no sparse Fenwick or spatial-total state. Tiny qualification only, real replay pending.'},indent=2)+'\n');print('INDEPENDENT_REBUILD_SCAN_PASS',count)
if __name__=='__main__':main()
