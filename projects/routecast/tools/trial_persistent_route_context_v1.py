"""Real endpoint updates; persistent search versus fresh context and exact audit."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from persistent_route_context_v1 import RouteContext
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'persistent_route_context_v1_2026-10-09';D.mkdir(exist_ok=False);bindings=closure([Path(__file__)])
base=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';tick=time.perf_counter();context=RouteContext(base);setup=time.perf_counter()-tick;bindings[str(base)]=sha(base);bindings[str(context.graph)]=context.digest;bindings.update(context.search.bindings);rows=[]
for step in range(1,4):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';queries=context.endpoints(ep);budgets={row['connection_id']:F(*row['exact_delay_s']) for row in json.loads(bp.read_text())};fresh=RouteContext(ep);assert fresh.endpoints(ep)==queries
 edge={eid:arc for arc,eid in context.audit.inventory.physical.arcs.items()}
 # Frozen subset checks changing input epochs, not full routing or performance.
 for cid in sorted(queries)[::172]:
  query=queries[cid];result=context.query(query['source'],query['sink'],budgets[cid],Counter(),set(),{});other=fresh.query(query['source'],query['sink'],budgets[cid],Counter(),set(),{});assert result==other
  if result['status']=='FOUND':
   path=[[query['source'],None]]
   for eid in result['physical_edge_ids']:
    u,v,s=edge[eid];assert u==path[-1][0];path.append([v,s])
   context.audit.validate({cid:path},{cid:query},{cid:budgets[cid]})
  rows.append(dict(step=step,cid=cid,status=result['status'],fresh_and_persistent_equal=True))
 fresh.close()
 for p in (ep,bp):bindings[str(p)]=sha(p)
context.close()
try:context.endpoints(base)
except ValueError:pass
else:raise AssertionError('closed context accepted endpoint update')
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,initial_setup_seconds=setup,closed_context_rejected=True,scope='Nine frozen real relaxed queries across three endpoint updates; persistent CSR/native search equals fresh context including physical paths and exact budgets. Constructor parses CSR and independent audit inventory separately once; no full routing/nativeSTA or workflow speedup claim.'),indent=2)+'\n');print(dict(rows=rows,initial_setup_seconds=setup),flush=True)
