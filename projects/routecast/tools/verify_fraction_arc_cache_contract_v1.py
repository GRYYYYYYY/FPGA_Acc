"""Exact cache differential, mutable caller isolation and unchanged audit AST."""
import ast
import json
import random
import sys
from fractions import Fraction
from pathlib import Path
from buffered_rc_node_classes import arc_delay
from fraction_arc_cache_v1 import FractionArcCache
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
pairs=[('verify_resident_demand_frame_physical_v3.py','verify_resident_demand_frame_physical_rc_cache_v4.py'),
       ('verify_resident_events_round_schedule_cache_v4.py','verify_resident_events_fraction_cache_v5.py')]
for original,candidate in pairs:
    old=(R/'tools'/original).read_text()
    new=(R/'tools'/candidate).read_text()
    new=new.replace('from fraction_arc_cache_v1 import FractionArcCache\n','')
    new=new.replace('delay_cache=FractionArcCache(classes,switches)\n','')
    new=new.replace('delay_cache(', 'arc_delay(classes,switches,')
    new=new.replace("which+'_physical_verification_rc_cache_v4.json'", "which+'_physical_verification.json'")
    assert ast.dump(ast.parse(old),include_attributes=False)==ast.dump(ast.parse(new),include_attributes=False)
rng=random.Random(20261008);checked=0
for context in range(200):
    classes=[[Fraction(rng.randrange(1000),rng.randrange(1,1000)),Fraction(rng.randrange(1000),rng.randrange(1,1000))] for _ in range(8)]
    switches={i:[Fraction(rng.randrange(1000),rng.randrange(1,1000)),Fraction(rng.randrange(1000),rng.randrange(1,1000))] for i in range(10)}
    snapshot=[tuple(x) for x in classes];saved={k:tuple(v) for k,v in switches.items()}
    cache=FractionArcCache(classes,switches)
    for step in range(200):
        c,s=rng.randrange(8),rng.randrange(10)
        assert cache(c,s)==arc_delay(snapshot,saved,c,s)
        checked+=1
    classes[0][0]+=999;switches[0][0]+=999
    assert cache(0,0)==arc_delay(snapshot,saved,0,0)
    for c,s in [(99,0),(0,99)]:
        try:arc_delay(snapshot,saved,c,s)
        except (IndexError,KeyError) as e:expected=type(e)
        else:raise AssertionError('expected invalid context rejection')
        try:cache(c,s)
        except expected:pass
        else:raise AssertionError('cache accepted invalid context')
bindings=closure([Path(__file__),*[R/'tools'/x for pair in pairs for x in pair]])
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/fraction_arc_cache_contract_v1_2026-10-08';D.mkdir(exist_ok=False)
result=dict(bindings=bindings,pass_all=True,contexts=200,exact_comparisons=checked,
    cached_audit_AST_equals_original_after_only_cache_and_output_path_substitution=True,
    scope='Component and AST checks only; complete real model output comparison and speed measurement remain unperformed')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'}))
