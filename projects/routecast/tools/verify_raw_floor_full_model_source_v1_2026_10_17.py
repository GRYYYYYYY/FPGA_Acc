"""Freeze the full-model boundary: only initial engine may change behavior."""
import ast,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/raw_floor_full_model_source_v1_2026-10-17';D.mkdir(exist_ok=False)
a=R/'tools/run_design_scoped_quotient_astar_proxy_budget_v1.py';b=R/'tools/run_design_scoped_raw_floor_proxy_budget_v1_2026_10_17.py'
def function(p):return next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='predict')
x,y=function(a),function(b)
def node(p,kind,test):return next(n for n in ast.walk(p) if isinstance(n,kind) and test(n))
rx=node(x,ast.For,lambda n:ast.unparse(n.target)=='round_index');ry=node(y,ast.For,lambda n:ast.unparse(n.target)=='round_index')
assert ast.dump(rx,include_attributes=False)==ast.dump(ry,include_attributes=False)
assert ast.get_source_segment(a.read_text(),rx)==ast.get_source_segment(b.read_text(),ry)
for name in ['own','rebuild']:
 xx=node(x,ast.FunctionDef,lambda n:n.name==name);yy=node(y,ast.FunctionDef,lambda n:n.name==name);assert ast.dump(xx,include_attributes=False)==ast.dump(yy,include_attributes=False)
for name in ['budgets']:
 xx=node(x,ast.Assign,lambda n:any(isinstance(t,ast.Name) and t.id==name for t in n.targets));yy=node(y,ast.Assign,lambda n:any(isinstance(t,ast.Name) and t.id==name for t in n.targets));assert ast.dump(xx,include_attributes=False)==ast.dump(yy,include_attributes=False)
assert not any(isinstance(n,ast.Name) and n.id=='search' for n in ast.walk(y))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
with (D/'verification.json').open('x') as f:json.dump(dict(bindings={str(p):sha(p) for p in [Path(__file__).resolve(),a,b]},all_pass=True,entire_feedback_round_loop_byte_identical=True,owner_and_ledger_rebuild_AST_equal=True,budget_formula_AST_equal=True,separate_initial_search_engine_removed=True,declared_additional_changes=['Initial grouped floor call uses raw-only quotient tree.','Quotient graph built from rc.increments instead of the removed floor engine tuple.','Explicit source/cost/large-pilot admission gates.','Initial native work separated from feedback counters; cache totals remain entire-process.','No-separate-engine memory annotation and initial-policy metadata.'],scope='Static source boundary only, not full correctness. Changed equal-cost initial paths may change ledger and feedback outcomes; new complete physical/event audits and quality evaluation are mandatory.'),f,indent=2);f.write('\n')
print('PASS entire feedback loop byte-identical and unchanged budget formula')
