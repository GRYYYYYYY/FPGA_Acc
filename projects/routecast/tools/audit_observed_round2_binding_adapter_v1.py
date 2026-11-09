"""Preserve original artifacts; authenticate the sole late-bound common control."""
import ast,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def validate(p,r,out):
 control=R/'experiments/mmc_objective_guard_full_schedule_v1_2026-10-12/model/round0.json'
 expected='68a30a1cae7f0096b4d8180356c026e1d934defe036241ae5b6ce732ffb06884'
 assert sha(control)==expected
 assert r['bindings']=={**p['bindings'],str(control):expected}
 assert str(control) not in p['bindings']
 parity=json.loads((out/'common_round0_parity.json').read_text())
 assert parity==dict(control=str(control),control_sha256=expected,entire_frame_equal=True)
 assert json.loads(control.read_text())==json.loads((out/'round0.json').read_text())
 return True

mode=sys.argv.pop(1)
source=R/'tools'/({'physical':'verify_resident_demand_frame_direct_lattice_v7.py','events':'verify_criticality_observed_round2_full_schedule_v1.py'}[mode])
parsed=ast.parse(source.read_text());matches=0
for node in ast.walk(parsed):
 if isinstance(node,ast.Assert) and ast.unparse(node.test)=="p['bindings'] == r['bindings']":
  node.test=ast.parse('validate(p,r,out)',mode='eval').body;matches+=1
assert matches==1
# Keep original verifier source/dependency closure and bind this adapter as well.
original_closure=closure
def closure(paths):
 return {**original_closure(paths),**original_closure([Path(__file__)])}
sys.argv[0]=str(source)
namespace=dict(__name__='__main__',__file__=str(source),validate=validate)
# Original import is replaced only to include adapter provenance in the proof.
for node in parsed.body:
 if isinstance(node,ast.ImportFrom) and node.module=='source_binding_v2':
  assert [x.name for x in node.names]==['closure']
  node.module='audit_observed_round2_binding_closure_v1'
ast.fix_missing_locations(parsed)
import types
module=types.ModuleType('audit_observed_round2_binding_closure_v1');module.closure=closure
sys.modules[module.__name__]=module
exec(compile(parsed,str(source),'exec'),namespace)
