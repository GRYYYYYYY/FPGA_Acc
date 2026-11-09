"""Exact AST derivation from frozen checked A* bridge, no kernel changes."""
import ast,copy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/raw_floor_adapter_source_contract_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=R/'tools/compiled_quotient_criticality_astar_v1.py';candidate=R/'tools/compiled_quotient_raw_floor_v1_2026_10_17.py'
def method(path,cls):
 t=ast.parse(path.read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==cls);return next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='expand')
f=copy.deepcopy(method(base,'Tree'));actual=method(candidate,'RawFloorTree')
f.args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='self'),ast.arg(arg='target')],kwonlyargs=[],kw_defaults=[],defaults=[])
f.body=ast.parse('criticality=Fraction(1,1)\nraw_budget=self.graph.raw_bound').body+f.body
changed=0
for i,n in enumerate(f.body):
 if isinstance(n,ast.If) and ast.unparse(n.test)=='type(congestion) is NativePrices':
  f.body[i:i+1]=ast.parse('base=g.zero\nprices=g.zero\nceiling=0').body;changed+=1;break
assert changed==1 and ast.dump(f,include_attributes=False)==ast.dump(actual,include_attributes=False)
contract=R/'experiments/compiled_quotient_astar_contract_v1_2026-10-17/verification.json';v=json.loads(contract.read_text());assert v['all_pass']
from compiled_quotient_criticality_astar_v1 import BINARY
for p in [base,BINARY]:assert sha(p)==v['bindings'][str(p)]
files=[Path(__file__).resolve(),base,candidate,BINARY,contract]
out=dict(bindings={str(p):sha(p) for p in files},all_pass=True,exact_AST_equal_after_only_declared_changes=True,changes=['Public signature removes external criticality/congestion/budget inputs.','Set exact Fraction(1,1) and proved simple-path raw_bound.','Replace price-context acquisition with existing zero buffers and ceiling0.'],unchanged=['Target/closed checks and checked integer arithmetic envelope.','Potential lookup and exact compiled kernel call.','Native status handling, complete path reconstruction and retained parent/arrival updates.','Compiled kernel bytes and checked A* bridge source.'],mathematical_scope='With p=q=1, node-price and static-price potential terms have zero weight. Every committed prefix on a globally shortest nonnegative raw path is raw-shortest; reused prefix seeds preserve multi-target exact floors. Randomized independent Dijkstra and real-floor comparisons remain separate evidence, not replaced by this source contract.',limitations='This adapter is used only on positive-capacity graphs admitted by pilots. Equal-cost paths may change. No full feedback or quality/timing proof.')
with (D/'verification.json').open('x') as stream:json.dump(out,stream,indent=2);stream.write('\n')
print('PASS exact raw-floor bridge derivation and unchanged native kernel')
