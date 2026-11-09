"""Execute auditor function bodies with independent tiny physical graph oracle."""
import ast,json,random,copy
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace as N
from pre_route_endpoints import sha
path=Path('tools/verify_criticality_present_guard_events_v1.py');new=ast.parse(path.read_text());old=ast.parse(Path('tools/verify_present_guard_events_v1.py').read_text())
def functions(module):return {n.name:n for n in module.body if isinstance(n,ast.FunctionDef)}
a=functions(old);b=functions(new)
for name in ['physical_path','ownership','rebuild']:assert ast.dump(a[name])==ast.dump(b[name])
source=ast.Module(body=[b['physical_path'],b['union_objective']],type_ignores=[]);env=dict(Fraction=Fraction)
exec(compile(source,str(path),'exec'),env)
edges=[N(source=0,sink=1,switch_id=0),N(source=1,sink=2,switch_id=1),N(source=1,sink=3,switch_id=2)]
queries={i:dict(connection_id=i,net_id=4,source=0,sink=s) for i,s in enumerate([2,3,2])}
records=[dict(q,budget_integer=10,answer=dict(physical_edge_ids=[0,1 if q['sink']==2 else 2],delay=3 if q['sink']==2 else 4)) for q in queries.values()]
env.update(xml=N(graph=N(nodes=[N(capacity=2) for _ in range(4)],edges=edges)),queries=queries,ids=list(range(4)),classes=[(Fraction(0),Fraction(0))]*4,switches=None,scale=1,arc_delay=lambda classes,switches,node,switch:Fraction([1,2,3][switch]))
rng=random.Random(139191);cases=0
for _ in range(400):
 crit={i:rng.choice([Fraction(0),Fraction(1),Fraction(1,3),Fraction(7,8)]) for i in queries};base=[rng.randrange(10) for _ in range(4)];price={u:rng.randrange(10) for u in range(4)};ledger={u:rng.randrange(1,6) for u in range(4)};oldnodes=set(rng.sample(range(4),rng.randrange(5)));weight=rng.randrange(1,5)
 env.update(criticalities=crit,node_base=base,prices=price,ledger=ledger,transaction_old_nodes=oldnodes,p=dict(price_unit_integer=weight))
 actual=env['union_objective'](records)
 users={1:[0,1,2],2:[0,2],3:[1]};expected=sum((crit[i]*records[i]['answer']['delay'] for i in queries),Fraction(0))
 for u,indices in users.items():
  other=ledger[u]-(u in oldnodes);present=max(0,other-2+1);cost=base[u]*(1+present)+weight*price[u];expected+=(1-max(crit[i] for i in indices))*cost
 assert actual==expected;cases+=1
bad=copy.deepcopy(records);bad[0]['answer']['delay']=4
try:env['union_objective'](bad)
except AssertionError:pass
else:raise AssertionError('bad physical raw report passed')
bad=copy.deepcopy(records);bad[0]['net_id']=5
try:env['union_objective'](bad)
except AssertionError:pass
else:raise AssertionError('bad query identity passed')
out=Path('experiments/criticality_event_auditor_objective_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve(),path.resolve(),Path('tools/verify_present_guard_events_v1.py').resolve()]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},cases=cases,independent_user_sets_exact_score_pass=True,physical_ownership_rebuild_function_AST_preserved=True,wrong_raw_and_identity_rejected=True,scope='Extracted actual auditor functions on tiny synthetic physical graph. Full script replay/XML loading/runtime branches remain unverified.'),indent=2)+'\n');print('CRITICALITY AUDITOR OBJECTIVE CONTRACT PASS',cases)
