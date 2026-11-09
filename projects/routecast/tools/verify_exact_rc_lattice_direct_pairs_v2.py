"""Independent edge-by-edge rational lattice reference and malformed storage."""
import json,random,sys
from array import array
from fractions import Fraction
from math import lcm
from pathlib import Path
from types import SimpleNamespace
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from immutable_xml_prediction_audit import CompactEdges
from exact_rc_lattice_direct_pairs_v2 import exact_scale
from exact_rc_lattice_unique_pairs_v1 import exact_scale as original
from source_binding_v2 import closure
rng=random.Random(101004);checked_edges=0
for i in range(200):
 n=rng.randrange(1,70);c=rng.randrange(1,8);s=rng.randrange(1,6);m=rng.randrange(0,500)
 classes=tuple((Fraction(rng.randrange(20),rng.randrange(1,50)),Fraction(rng.randrange(20),rng.randrange(1,50))) for _ in range(c))
 switches={j:(Fraction(rng.randrange(20),rng.randrange(1,50)),Fraction(rng.randrange(20),rng.randrange(1,50))) for j in range(s)}
 ids=array('Q',[rng.randrange(c) for _ in range(n)]);src=array('Q',[rng.randrange(n) for _ in range(m)]);dst=array('Q',[rng.randrange(n) for _ in range(m)]);sw=array('Q',[rng.randrange(s) for _ in range(m)])
 edges=CompactEdges(src,dst,sw);expected=1
 for k in ids:
  r,cap=classes[k];expected=lcm(expected,(r*cap/2).denominator)
 pairs=set()
 for node,si in zip(dst,sw):
  r,cap=classes[ids[node]];rs,delay=switches[si]
  expected=lcm(expected,(delay+rs*cap+r*cap/2).denominator);pairs.add((ids[node],si))
 assert exact_scale(ids,classes,switches,edges)==original(ids,classes,switches,edges)==(expected,len(pairs))
 generic=[SimpleNamespace(source=u,sink=v,switch_id=j) for u,v,j in zip(src,dst,sw)]
 assert exact_scale(ids,classes,switches,generic)==(expected,len(pairs))
 checked_edges+=m
# Detect corrupted compact metadata before any zip truncation can hide edges.
rejected=[]
for name,replacement in [('writable',memoryview(array('Q',[0]))),('short',memoryview(b'').cast('Q')),('wrongformat',memoryview(b'x'))]:
 edges=CompactEdges(array('Q',[0]),array('Q',[0]),array('Q',[0]));edges.switch=replacement
 try:exact_scale([0],((Fraction(1),Fraction(1)),),{0:(Fraction(1),Fraction(1))},edges)
 except ValueError:rejected.append(name)
 else:raise AssertionError(name)
D=R/'experiments/exact_rc_lattice_direct_pairs_contract_v2_2026-10-10';D.mkdir()
(D/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),random_contexts=200,independent_edge_formula_checks=checked_edges,original_helper_and_generic_API_equal=True,rejected=rejected,pass_all=True,scope='Independent rational formula and complete small-graph scans. No full MMC audit or timing gain proof.'),indent=2)+'\n')
print('PASS',checked_edges,'independent exact lattice edge formula checks',rejected)
