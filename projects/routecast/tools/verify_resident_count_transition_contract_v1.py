"""Check the candidate's exact count-update block and all feedback write sites."""
import ast,json,random,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
p=R/'tools/run_resident_soft_demand_radix_count_v4.py';tree=ast.parse(p.read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict')
loop=next(n for n in fn.body if isinstance(n,ast.For) and ast.unparse(n.target)=='round_index')
stores=[n for n in ast.walk(loop) if isinstance(n,ast.Subscript) and isinstance(n.ctx,ast.Store) and isinstance(n.value,ast.Name) and n.value.id=='records']
assert len(stores)==1 and ast.unparse(stores[0])=='records[net]'
updates=[n for n in ast.walk(loop) if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='record_count']
assert len(updates)==1 and ast.unparse(updates[0])=='record_count += len(candidate) - len(records[net])'
commit=next(n for n in ast.walk(loop) if isinstance(n,ast.If) and ast.unparse(n.test)=='not bad')
i=commit.body.index(updates[0]);assign=commit.body[i+1]
assert isinstance(assign,ast.Assign) and ast.unparse(assign)=='records[net] = candidate'
code=compile(ast.Module(body=[updates[0],assign],type_ignores=[]),str(p),'exec')
rng=random.Random(74017);scope=dict(records={n:list(range(n%7)) for n in range(17)})
scope['record_count']=sum(map(len,scope['records'].values()))
for step in range(2000):
 scope['net']=rng.randrange(17);scope['candidate']=list(range(rng.randrange(25)))
 if step%3:exec(code,scope)
 assert scope['record_count']==sum(map(len,scope['records'].values()))
 # Retained transactions leave both the records and counter untouched.
D=R/'experiments/resident_count_transition_contract_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={str(q):sha(q) for q in [p,Path(__file__)]}
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,extracted_candidate_transition_and_full_sum_equal_steps=2000,unique_feedback_records_write_site=True,scope='Local cardinality transition and feedback write-site contract, with varied candidate lengths and retained steps. Not complete model/physical/event parity or performance evidence.'),indent=2)+'\n')
print('PASS count transition contract 2000 steps')
