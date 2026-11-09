"""Execute original and candidate AST projection blocks on malformed/valid routes."""
import ast,json,random,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
paths=[R/'tools/verify_ultraembedded_mmc_native_cold_v1.py',R/'tools/verify_ultraembedded_mmc_native_name_set_v2.py']
codes=[]
for p in paths:
 tree=ast.parse(p.read_text());nodes=[]
 for n in tree.body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['required_net_names','observed'] for t in n.targets):nodes.append(n)
 assert len(nodes)==(1 if len(codes)==0 else 2)
 codes.append(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'))
rng=random.Random(261008);outcomes=[]
for i in range(300):
 # Required names are strings, as in authenticated real endpoint inventories.
 ep=dict(net_names={str(n):rng.choice(['a','b','c']) for n in range(rng.randrange(8))})
 names={n:rng.choice(['a','b','c','ignored']) for n in range(6)}
 connections=[dict(net_id=rng.randrange(7 if i%5==0 else 6),source=rng.randrange(3),sink=rng.randrange(5)) for _ in range(rng.randrange(20))]
 if connections and i%3==0:connections+=connections[:2]
 results=[]
 for code in codes:
  scope=dict(Counter=Counter,names=names,ep=ep,a=dict(connections=connections))
  try:
   exec(code,scope);results.append(('ok',scope['observed']))
  except KeyError as e:results.append(('KeyError',e.args))
 assert results[0]==results[1],i
 outcomes.append(results[0][0])
D=R/'experiments/native_name_membership_contract_v1_2026-10-08';D.mkdir(exist_ok=False)
bindings={str(p):sha(p) for p in [Path(__file__),*paths]}
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,actual_AST_projection_differential_cases=300,outcomes=dict(Counter(outcomes)),scope='Valid string-valued name maps, duplicated names/connections, empty sets/routes, ignored names and missing route NET identities; exact Counter or KeyError outcomes. No XML or runtime proof.'),indent=2)+'\n')
print('PASS actual AST name projection differential',dict(Counter(outcomes)))
