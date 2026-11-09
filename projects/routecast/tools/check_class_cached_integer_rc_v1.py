"""Random exact-class context parity; unused electrical classes must not change lattice."""
import sys,json,random
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC as Original
from class_cached_integer_rc_v1 import IntegerRC
from source_binding_v2 import closure
rng=random.Random(613);
for trial in range(200):
 n=rng.randrange(1,30);classes=[(Fraction(rng.randrange(20),rng.choice([3,5,7])),Fraction(rng.randrange(20),rng.choice([11,13]))) for _ in range(6)];classes.append((Fraction(1,1009),Fraction(1,1013)))
 nc=[rng.randrange(6) for _ in range(n)];switches={i:(Fraction(rng.randrange(20),17),Fraction(rng.randrange(20),19)) for i in range(3)};f={'node_ids':list(range(n)),'row_offsets':[0],'edge_ids':[],'dest_ranks':[],'switch_ids':[]}
 for u in range(n):
  for _ in range(rng.randrange(5)):f['edge_ids'].append(len(f['edge_ids']));f['dest_ranks'].append(rng.randrange(n));f['switch_ids'].append(rng.randrange(3))
  f['row_offsets'].append(len(f['edge_ids']))
 ar=ExactBufferedRC(f,nc,classes,switches);br=ExactBufferedRC(f,nc,classes,switches);a=IntegerRC(ar);b=Original(br);assert a.scale==b.scale and a.increments==b.increments;assert all(a.initial(i)==b.initial(i) for i in range(n))
 for invalid in [-1,n,True,1.5]:
  try:a.initial(invalid)
  except ValueError:pass
  else:raise AssertionError('invalid node accepted')
out=R/'experiments/class_cached_integer_rc_contract_v1_2026-10-07';out.mkdir();(out/'verification.json').write_text(json.dumps({'bindings':closure([Path(__file__)]),'random_exact_class_cases':200,'unused_class_scale_and_all_increments_initials_invalid_nodes_pass':True},indent=2)+'\n');print('200 exact class contexts PASS')
