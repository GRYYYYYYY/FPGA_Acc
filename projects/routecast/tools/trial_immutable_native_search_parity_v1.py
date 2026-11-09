"""Full four-step current-branch constrained search parity, all2064 queries."""
import json,time
from fractions import Fraction as F
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from immutable_endpoint_context_v1 import ImmutableEndpointContext
from load_complete_route_state_v1 import load_complete
from native_bounded_wire_search_v1 import NativeBoundedSearch as Reference
from native_immutable_bounded_search_v1 import NativeBoundedSearch as Owned
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'immutable_native_search_parity_v1_2026-10-09';D.mkdir(exist_ok=False)
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';a=load_endpoints(ep0);ctx=ImmutableEndpointContext.build(ep0);b=ctx.load(ep0);length={}
for n,node in enumerate(b[2]):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
ref=Reference(a[4],length);owned=Owned(b[4],length);bindings={**ref.bindings,**owned.bindings};rows=[];tick=time.perf_counter()
try:
 for step in range(4):
  ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());route=E/f'adder_wire_guard_matched_cold_v5_2026-10-08/step_{step}/output.route';ctx.load(ep);state,audits,ledger=load_complete(route,meta,b[2],b[3],b[4]);budgetpath=E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json';budgets={v['connection_id']:F(*v['exact_delay_s']) for v in json.loads(budgetpath.read_text())};statuses=Counter()
  for cid,q in sorted(ledger.queries.items()):
   kept,parents=ledger.view(cid);outside=Counter({node:c-int(node in ledger.nodes[q['net_id']]) for node,c in ledger.occupancy.items()});value=budgets[cid]*b[4].scale;allowance=sum(ledger.wire.values())-sum(w for net,w in ledger.wire.items() if net!=q['net_id'])-sum(length.get(n,0) for n in kept)
   args=(q['source'],q['sink'],value.numerator//value.denominator,outside,kept,parents,1000000,allowance+1)
   x=ref.query(*args);y=owned.query(*args);assert x==y,(step,cid);statuses[y['status']]+=1
  rows.append(dict(step=step,connections=len(ledger.queries),all_result_fields_equal=True,status_counts=dict(statuses)))
  for p in (ep,route,budgetpath):bindings[str(p)]=sha(p)
finally:ref.close();owned.close()
assert all(sha(p)==h for p,h in bindings.items())
for name in ('trial_immutable_native_search_parity_v1.py','native_immutable_bounded_search_v1.py','immutable_endpoint_context_v1.py','native_bounded_wire_search_v1.py','load_complete_route_state_v1.py'):bindings[str(R/'tools'/name)]=sha(R/'tools'/name)
out=dict(bindings=bindings,rows=rows,query_component_seconds=time.perf_counter()-tick,scope='All2064 fixed-current-state branch queries match original path/cost/delay/status/search counters exactly. Native arrays copied once per handle and lifetime owned; no production chain or speedup proof.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
