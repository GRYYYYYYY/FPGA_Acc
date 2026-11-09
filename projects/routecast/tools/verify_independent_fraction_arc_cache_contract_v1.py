"""Independent Fraction reference checks, repeated hits and context isolation."""
import json,sys,random
from pathlib import Path
from fractions import Fraction as F
from types import MappingProxyType
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from independent_fraction_arc_context_v2 import _register,arc_delay,diagnostics
from pre_route_endpoints import sha
from source_binding_v2 import closure
rng=random.Random(20261010);contexts=[];checked=0
for index in range(200):
 classes=tuple((F(rng.randrange(40),rng.randrange(1,15)),F(rng.randrange(40),rng.randrange(1,15))) for _ in range(5))
 switches=MappingProxyType({i:(F(rng.randrange(40),rng.randrange(1,15)),F(rng.randrange(40),rng.randrange(1,15))) for i in range(7)})
 _register(classes,switches);contexts.append((classes,switches))
for repeat in range(3):
 for classes,switches in reversed(contexts):
  for c in range(5):
   for s in range(7):
    resistance,capacitance=classes[c];sr,intrinsic=switches[s]
    expected=(sr+resistance/F(2))*capacitance+intrinsic
    assert arc_delay(classes,switches,c,s)==expected;checked+=1
bad=0
for classes,switches in [([],MappingProxyType({})),((),{}),(((1,2),),MappingProxyType({}))]:
 try:_register(classes,switches)
 except TypeError:bad+=1
 else:raise AssertionError('mutable/nonexact registration accepted')
try:arc_delay(tuple([(F(1),F(2))]),MappingProxyType({0:(F(3),F(4))}),0,0)
except ValueError:bad+=1
else:raise AssertionError('unregistered context accepted')
stats=diagnostics();assert stats['contexts']==200 and stats['misses']==stats['entries']==7000 and stats['hits']==14000
D=R/'experiments/independent_fraction_arc_cache_contract_v1_2026-10-10';D.mkdir()
(D/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),full_reference_fraction_checks=checked,invalid_context_rejections=bad,diagnostics=stats,pass_all=True,scope='Scalar memoization and registered context isolation only; arbitrary externally mutable backing mappings are unsupported. Production registration is restricted to original privately owned immutable loader output. No complete graph/path/event equivalence or speed evidence.'),indent=2)+'\n')
print('PASS scalar Fraction cache',checked,bad,stats)
