"""Show why fixed-tree fallback cannot replace whole-NET joint fallback."""
import json
from pathlib import Path
from fractions import Fraction
from criticality_shared_tree_raw_fallback_v1 import Tree
from pre_route_endpoints import sha
fields=dict(row_offsets=[0,2,3,4,4],dest_ranks=[1,2,3,1]);inc=[10,1,1,1]
tree=Tree(fields,inc,[0]*4,0)
a=tree.expand(1,Fraction(1,4),[0,0,100,0],20)
assert a['committed'] and not a['used_raw_fallback'] and a['raw']==10
before=dict(tree.arrival),dict(tree.parents)
b=tree.expand(3,Fraction(1,4),[0,0,100,0],4)
assert not b['committed'] and b['raw']==11 and b['status']=='NO_FEASIBLE_FIXED_TREE_EXTENSION'
assert (tree.arrival,tree.parents)==before
# Independently explicit alternative whole tree: 0->2->1->3.
alternative={2:(0,1),1:(2,3),3:(1,2)}
arrivals={0:0}
for v in [2,1,3]:
 u,slot=alternative[v];assert fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1] and fields['dest_ranks'][slot]==v
 arrivals[v]=arrivals[u]+inc[slot]
assert arrivals[1]==2<=20 and arrivals[3]==3<=4
out=Path('experiments/criticality_whole_net_backtrack_boundary_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),Path(__file__).with_name('criticality_shared_tree_raw_fallback_v1.py').resolve(),Path(__file__).with_name('criticality_shared_tree_reference_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},fixed_tree_rejects_but_valid_whole_net_alternative_exists=True,ordered_first_sink_raw=10,fixed_tree_second_sink_minimum_raw=11,alternative_sink_raw=[2,3],budgets=[20,4],required_followup='Retain original whole-NET joint budget fallback and overflow/owner transaction gates; do not interpret fixed-tree failure as NET infeasibility.'),indent=2)+'\n')
print('WHOLE NET BACKTRACK BOUNDARY PASS; JOINT FALLBACK STILL REQUIRED')
