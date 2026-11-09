"""Complete candidate census; distinguish legacy budgets from floor-derived ablations."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/mcnc_original_budget_candidates_v1_2026-10-08'
D.mkdir(exist_ok=False)
base=R/'experiments/mcnc_tree_floor_development_v1_2026-10-07'
protocol=json.loads((base/'protocol.json').read_text())
receipt=json.loads((base/'receipt.json').read_text())
assert receipt['protocol_sha256']==sha(base/'protocol.json')
bindings={str(p):sha(p) for p in (Path(__file__),base/'protocol.json',base/'receipt.json')}
assert all(sha(p)==h for p,h in {**protocol['inputs'],**protocol['sources']}.items())
bindings.update(protocol['inputs']);bindings.update(protocol['sources'])
rows=[]
for name in protocol['cases']:
 ep=R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json'
 fp=base/f'{name}_floors.json';cp=base/f'{name}_tree1_floor1.json'
 for p in (ep,fp,cp):bindings[str(p)]=sha(p)
 e=json.loads(ep.read_text());c=json.loads(cp.read_text());fs=json.loads(fp.read_text())
 archived=next(x for x in receipt['rows'] if x['name']==name and x['tree'] and x['floor_budget'])
 assert sha(cp)==archived['candidate_sha256']
 floors={(x['source'],x['sink']):x['minimum_integer'] for x in fs}
 assert len(floors)==len(fs)
 queries={q['connection_id']:q for q in e['connections']}
 assert len(queries)==len(e['connections'])==c['required_connections']
 assert set(floors)=={(q['source'],q['sink']) for q in queries.values()}
 limits={};details=[]
 for cid,q in sorted(queries.items()):
  floor=floors[q['source'],q['sink']];assert floor>=0
  legacy=c['scale']//10**9;develop=max(legacy,(3*floor+1)//2)
  limits[cid]=develop
  details.append(dict(connection_id=cid,minimum_ns=str(F(floor*10**9,c['scale'])),legacy_budget_ns=str(F(legacy*10**9,c['scale'])),legacy_floor_exceeds_budget=floor>legacy,development_budget_ns=str(F(develop*10**9,c['scale'])),development_budget_raised=develop>legacy))
 for r in c['records']:
  assert r['floor_integer']==floors[r['source'],r['sink']]
  assert r['budget_integer']==limits[r['connection_id']]
 failure=c['failure'];assert failure is not None
 assert failure['budget_integer']==limits[failure['query']['connection_id']]
 blockers=[d for d in details if d['legacy_floor_exceeds_budget']]
 raised=[d for d in details if d['development_budget_raised']]
 assert blockers and c['status']=='INCOMPLETE_NOT_PUBLISHABLE'
 rows.append(dict(name=name,connections=len(queries),legacy_floor_exceedances=len(blockers),legacy_blocker_ids=[x['connection_id'] for x in blockers],development_raised_connections=len(raised),development_still_incomplete=True,development_first_failure=failure,eligible_as_original_budget_positive_case=False,rows=details))
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,rows=rows,positive_original_budget_candidates=0,
 scope='Complete arithmetic/provenance census over archived input-only floor values and authenticated ablation outputs. No fresh optimality certificate replay: legacy exceedances are screening evidence, not a new certified skip. Floor-derived budgets were explicitly widened post-outcome; cannot validate original-budget continue. All cases retained; no routing rerun, native timing, unseen-family or speedup claim.')
(D/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
for x in rows:print(x['name'],x['connections'],'legacy floor exceedances',x['legacy_floor_exceedances'],'raised development budgets',x['development_raised_connections'])
