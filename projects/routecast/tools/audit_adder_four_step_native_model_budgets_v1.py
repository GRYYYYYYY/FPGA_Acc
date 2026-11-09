"""Complete four-step archived native audit against existing model-baseline budgets."""
import json
from fractions import Fraction as F
from pathlib import Path
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_four_step_native_model_budgets_v1_2026-10-08';D.mkdir(exist_ok=False)
P=E/'adder_budget_provenance_v1_2026-10-08/verification.json';v=json.loads(P.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings={**v['bindings'],str(P):sha(P)};rows=[];inv=None
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json'
 meta=json.loads(ep.read_text());g=Path(meta['inputs']['graph']['path'])
 route=g.with_name('design.route') if step==0 else E/f'native_resume_all_inventory_adder_step{step}_cold_2026-10-07/first/output.route'
 if inv is None:inv=read(g,meta['graph_sha256'])
 assert inv.digest==meta['graph_sha256']
 bp=E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json';budgets={b['connection_id']:b for b in json.loads(bp.read_text())}
 state,delays,proof=load(route,meta,inv);assert len(delays)==len(budgets)==516
 results=[];fail=[]
 for x in delays:
  cid=x['connection_id'];b=budgets[cid];q=next(q for q in meta['connections'] if q['connection_id']==cid)
  assert all(b[k]==q[k] for k in ('connection_id','net_id','source','sink'))
  delay=F(x['delay_seconds']);limit=F(*b['exact_delay_s']);ok=delay<=limit
  results.append(dict(connection_id=cid,delay_seconds=str(delay),budget_seconds=str(limit),budget_pass=ok,physical_edge_ids=x['physical_edge_ids']))
  if not ok:fail.append(cid)
 out=D/f'step_{step}_proof.json';out.write_text(json.dumps(dict(rows=sorted(results,key=lambda x:x['connection_id']),physical=proof,violation_ids=sorted(fail)),indent=2)+'\n')
 for f in (ep,route,bp,out):bindings[str(f)]=sha(f)
 bindings.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
 row=dict(step=step,connections=len(delays),physical_pass=True,capacity_overflow=proof['overflow_units'],budget_safe=len(delays)-len(fail),violation_ids=sorted(fail),model_budget_admitted=not fail);rows.append(row);print(step,'full516','budget failures',len(fail),flush=True)
assert all(sha(f)==h for f,h in bindings.items())
for n in ('audit_adder_four_step_native_model_budgets_v1.py','unified_rr_audit_inventory_v2.py','direct_retained_route_import_v1.py','stream_native_route_audit_unified_v1.py','native_route_ledger_import_compact.py','path_rc.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,total_connections=2064,scope='All four archived original-placement native results, exact model-baseline budgets unchanged; complete physical/endpoint/uniqueArc/capacity checks. No fresh native run, user clock acceptance, positive floor authority or unseen-family/runtime gain.'),indent=2)+'\n')
