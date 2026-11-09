"""Inherited full replay body preservation plus new-objective contract binding."""
import ast,json
from pathlib import Path
from pre_route_endpoints import sha
R=Path.cwd();old=R/'tools/verify_present_guard_events_v1.py';new=R/'tools/verify_criticality_present_guard_events_v1.py';a=ast.parse(old.read_text());b=ast.parse(new.read_text())
fa={x.name:x for x in a.body if isinstance(x,ast.FunctionDef)};fb={x.name:x for x in b.body if isinstance(x,ast.FunctionDef)}
for name in ['physical_path','ownership','rebuild']:assert ast.dump(fa[name])==ast.dump(fb[name])
def replay(module):return next(x for x in module.body if isinstance(x,ast.For) and isinstance(x.target,ast.Tuple) and [getattr(v,'id',None) for v in x.target.elts]==['index','roundrow'])
assert ast.dump(replay(a))==ast.dump(replay(b)),'full round replay body changed'
class RestoreMetadata(ast.NodeTransformer):
 def visit_Call(self,node):
  node=self.generic_visit(node)
  if isinstance(node.func,ast.Name) and node.func.id=='Fraction' and len(node.args)==1:
   v=node.args[0]
   if isinstance(v,ast.Subscript) and isinstance(v.value,ast.Name) and v.value.id=='meta' and isinstance(v.slice,ast.Constant) and v.slice.value in ['old_score','chosen_score']:
    v.slice.value={'old_score':'old_union_cost','chosen_score':'chosen_union_cost'}[v.slice.value];return v
  return node
assert ast.dump(fa['audit_fallback'])==ast.dump(RestoreMetadata().visit(fb['audit_fallback']))
P=R/'experiments/criticality_event_auditor_objective_contract_v1_2026-10-10/verification.json';proof=json.loads(P.read_text());assert proof['cases']==400 and all(sha(p)==h for p,h in proof['bindings'].items())
O=R/'experiments/criticality_event_auditor_qualification_v1_2026-10-10';O.mkdir();bindings={**proof['bindings'],str(P):sha(P),str(Path(__file__).resolve()):sha(Path(__file__))}
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,full_round_event_replay_AST_exactly_preserved=True,fallback_membership_budget_guard_AST_preserved_except_score_metadata=True,physical_owner_rebuild_AST_preserved=True,scope='Source inheritance and tiny objective contract only. Runtime full new model receipt validation still required.'),indent=2)+'\n');print('FULL CRITICALITY AUDITOR SOURCE QUALIFICATION PASS')
