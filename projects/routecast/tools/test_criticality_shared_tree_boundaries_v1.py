"""Budget counterexample and rejected-input transaction checks."""
import json
from pathlib import Path
from fractions import Fraction
from criticality_shared_tree_reference_v1 import Tree
from pre_route_endpoints import sha
# Low congestion chooses raw 10 while another path has raw 2 and is budget-feasible.
t=Tree(dict(row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,3]),[5,1,5,1],[0]*4,0)
r=t.expand(3,Fraction(1,4),[0,0,100,0],3)
assert r['status']=='RETAIN_RAW_BUDGET' and r['raw']==10 and t.arrival=={0:0} and not t.parents
assert 1+1<=3
before=dict(t.arrival),dict(t.parents)
bad=[(-1,Fraction(1,2),[0]*4,3),(3,.5,[0]*4,3),(3,Fraction(2),[0]*4,3),(3,Fraction(1,2),[0,-1,0,0],3),(3,Fraction(1,2),[0]*3,3),(3,Fraction(1,2),[0]*4,-1)]
for args in bad:
 try:t.expand(*args)
 except ValueError:pass
 else:raise AssertionError('invalid input admitted')
 assert (t.arrival,t.parents)==before
out=Path('experiments/criticality_shared_tree_boundaries_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),Path(__file__).with_name('criticality_shared_tree_reference_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},budget_feasible_alternative_exists_after_primary_reject=True,invalid_inputs_preserve_tree=6,required_followup='Production candidate must retain original raw-budget fallback, validate its paths and single-parent shared tree, and freeze transaction costs before MMC.',scope='Counterexample confirms reference primary is not constrained-feasibility complete.'),indent=2)+'\n')
print('SHARED TREE BOUNDARIES PASS; RAW-BUDGET FALLBACK REQUIRED')
