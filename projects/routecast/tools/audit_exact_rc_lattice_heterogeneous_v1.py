"""Heterogeneous electrical contract fixture; topology is synthetic, parameters archived."""
import json,random
from fractions import Fraction
from math import lcm
from pathlib import Path
from types import SimpleNamespace
from buffered_rc_node_classes import arc_delay
from exact_rc_lattice_unique_pairs_v1 import exact_scale
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];P=R/'experiments/stereo_prospective_validation_2026-10-05/exact_buffered_rc_classes_v2';receipt=json.loads((P/'receipt.json').read_text());context=P/'electrical_context.json'
assert sha(context)==receipt['outputs'][context.name]
a=json.loads(context.read_text());classes=[tuple(Fraction(*v) for v in row) for row in a['node_rc_classes']];switches={int(k):tuple(Fraction(*v) for v in row) for k,row in a['switches'].items()};assert len(classes)==477 and len(switches)==4
rows=[]
for seed in range(8):
 rng=random.Random(seed);ids=list(range(len(classes)));rng.shuffle(ids)
 edges=[SimpleNamespace(sink=n,switch_id=s) for n in range(len(ids)) for s in switches for _ in range(1+rng.randrange(7))];rng.shuffle(edges)
 old=1
 for n in ids:
  r,c=classes[n];old=lcm(old,(r*c/2).denominator)
 for e in edges:old=lcm(old,arc_delay(classes,switches,ids[e.sink],e.switch_id).denominator)
 new,pairs=exact_scale(ids,classes,switches,edges);assert old==new and pairs==477*4
 assert all((arc_delay(classes,switches,c,s)*new).denominator==1 for c in ids for s in switches)
 rows.append(dict(seed=seed,edges=len(edges),unique_pairs=pairs,scale=new,equal=True))
D=R/'experiments/exact_rc_lattice_heterogeneous_v1_2026-10-09';D.mkdir(exist_ok=True)
out=dict(bindings={str(p):sha(p) for p in [context,P/'receipt.json',Path(__file__),R/'tools/exact_rc_lattice_unique_pairs_v1.py']},all_eight_heterogeneous_contract_cases_pass=True,rows=rows,scope='Synthetic topology fixtures using authenticated archived 477 RC classes and four switch parameters, duplicated and reordered. All class/switch combinations exercised, including combinations not necessarily present in original graph. Not a full stereo graph audit, unseen-family evaluation, routing or performance result.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS heterogeneous contract',len(rows),'cases',len(classes),'classes',len(switches),'switches')
