"""Exercise seed sharing, rejection atomicity, and subsequent tree attachment."""
from fractions import Fraction
from criticality_shared_tree_sparse_reference_v3 import Graph
from retained_criticality_tree_seed_v1 import seed
f={'row_offsets':[0,2,4,5,6,6], 'dest_ranks':[1,2,3,2,3,4]}
g=Graph(f,[2,3,4,1,3,2],[0]*5)
t=g.tree(0)
assert seed(t,[(3,[0,2],6),(1,[0],2)])==frozenset({0,1,3})
assert t.arrival=={0:0,1:2,3:6}
a=dict(t.arrival);p=dict(t.parents)
r=t.expand(4,Fraction(1,2),{},7)
assert not r['committed'] and t.arrival==a and t.parents==p
r=t.expand(4,Fraction(1,2),{},8)
assert r['committed'] and r['attach']==3 and r['path_slots']==(0,2,5)
for paths in [[(3,[0,2],5)],[(3,[0,2],6),(3,[1,4],6)],[(3,[0,4],9)],[(4,[0,2],9)],[(3,[0,2],-1)]]:
 t=g.tree(0);a=dict(t.arrival);p=dict(t.parents)
 try:seed(t,paths)
 except ValueError:pass
 else:raise AssertionError('invalid import accepted')
 assert t.arrival==a and t.parents==p
print('PASS retained path sharing, atomic rejection, attachment and budget retention')
