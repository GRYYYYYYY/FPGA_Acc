import pathlib,json,hashlib,itertools,random,math
from shortest_NET_tree_ensemble_v1 import prepare,materialize
from NET_predecessor_mandatory_channels_v1 import mandatory
R=pathlib.Path(__file__).resolve().parents[1];rng=random.Random(1019);checked=assignments=unreachable=0
for i in range(300):
 edges=[(eid,rng.randrange(7),rng.randrange(7),rng.randrange(4)) for eid in range(18)]
 try:p=prepare(edges,0,[5,6])
 except ValueError:unreachable+=1;continue
 keys=sorted(p['choices']);count=math.prod(len(p['choices'][n]) for n in keys);assert count<=100000;common=None
 for values in itertools.product(*(p['choices'][n] for n in keys)):
  nodes=set(materialize(p,dict(zip(keys,values)))['nodes']);common=nodes if common is None else common&nodes;assignments+=1
 assert set(mandatory(p))==common;checked+=1
O=R/'experiments/NET_predecessor_mandatory_core_v1_2026-10-19';O.mkdir();files=[pathlib.Path(__file__).resolve(),R/'tools/NET_predecessor_mandatory_channels_v1.py',R/'tools/shortest_NET_tree_ensemble_v1.py'];(O/'verification.json').write_text(json.dumps(dict(status='NET_UNION_DOMINATORS_EQUAL_EXHAUSTIVE_ALL_TREE_INTERSECTION',bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},random_graphs=300,reachable_NETs=checked,unreachable=unreachable,exhaustive_assignments=assignments,scope='All local-parent choices in supplied DAG only. Does not establish supplied support completeness for the full RR graph, unconstrained routability or native minimum-cost feasibility.'),indent=2)+'\n');print('DOMINATOR PASS',checked,assignments)
