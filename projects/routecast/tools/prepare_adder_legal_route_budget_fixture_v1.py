"""Known-feasible positive control; budgets defined by legal native witness route."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_legal_route_budget_fixture_v1_2026-10-09';D.mkdir(exist_ok=False);ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);bindings=closure([Path(__file__)]);plans=[]
roots=[E/'adder_budget_reject_fallback_cold_v1_2026-10-08',E/'adder_budget_reject_fallback_canonical_v1_2026-10-08']
for root in roots:
 p=root/'receipt.json';doc=json.loads(p.read_text());assert all(sha(f)==h for f,h in doc['bindings'].items());bindings.update(doc['bindings']);bindings[str(p)]=sha(p)
for step in range(4):
 ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());route=roots[0]/f'step_{step}/output.route';state,rows,ledger=load_complete(route,meta,nodes,f,rc);queries={q['connection_id']:q for q in meta['connections']};budgets=[]
 for row in rows:
  cid=row['connection_id'];delay=F(row['delay_integer'],rc.scale);q=queries[cid];budgets.append(dict(connection_id=cid,net_id=q['net_id'],source=q['source'],sink=q['sink'],exact_delay_s=[delay.numerator,delay.denominator],provenance='LEGAL_NATIVE_WITNESS_EQUALITY_POSITIVE_CONTROL'))
 bp=D/f'step_{step}_budgets.json';bp.write_text(json.dumps(budgets,indent=2)+'\n');sp=D/f'step_{step}_state.json';sp.write_text(json.dumps(dict(state={str(cid):path for cid,path in state.items()},node_occupancy={str(n):c for n,c in ledger.occupancy.items()},wire=sum(ledger.wire.values())),indent=2)+'\n')
 for p in (ep,route,bp,sp):bindings[str(p)]=sha(p)
 plans.append(dict(step=step,endpoints=str(ep),budgets=str(bp),state=str(sp),witness_route=str(route),connections=len(state)))
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,plans=plans,scope='Separate positive control derived from already legal full native route; not independent targets, heldout benchmark, original budget repair, userclock or speedup evidence.'),indent=2)+'\n');print([p['connections'] for p in plans])
