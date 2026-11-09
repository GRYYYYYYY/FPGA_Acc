"""Three complete history runs in one persistent context, against authenticated oracle."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from persistent_route_context_v1 import RouteContext
from persistent_net_history_v1 import generate
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'persistent_net_history_v1_2026-10-09';D.mkdir(exist_ok=False)
bindings=closure([Path(__file__)]);base=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';tick=time.perf_counter();ctx=RouteContext(base);setup=time.perf_counter()-tick;bindings[str(base)]=sha(base);bindings[str(ctx.graph)]=ctx.digest;bindings.update(ctx.search.bindings);rows=[]
prefixes=['fresh_history_workflow_v1','history_step2_v1','history_step3_v1']
for step,prefix in enumerate(prefixes,1):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json'
 op=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_0_state.json' if step==1 else E/f'{prefixes[step-2]}_stage_2_2026-10-09/result.json'
 old={int(cid):path for cid,path in json.loads(op.read_text())['state' if step==1 else 'paths'].items()};q=ctx.endpoints(ep);budgets={row['connection_id']:F(*row['exact_delay_s']) for row in json.loads(bp.read_text())}
 before=(ctx.audit.hits,ctx.audit.misses);tick=time.perf_counter();result=generate(ctx,q,budgets,old);elapsed=time.perf_counter()-tick
 out=D/f'step_{step}_result.json';out.write_text(json.dumps(result,indent=2)+'\n')
 oracle=E/f'{prefix}_stage_0_2026-10-09/result.json'
 for name in ('verification.json','independent_verification.json'):
  p=oracle.with_name(name);doc=json.loads(p.read_text())
  for filename,digest in doc['bindings'].items():assert sha(filename)==digest
  bindings[str(p)]=sha(p)
 assert json.loads(out.read_text())==json.loads(oracle.read_text())
 for p in (ep,bp,op,out,oracle):bindings[str(p)]=sha(p)
 rows.append(dict(step=step,admitted_connections=result['attempts'][0]['admitted_connections'],events=len(result['attempts'][0]['events']),entire_result_equals_authenticated_original=True,production_seconds=elapsed,cache_hits=ctx.audit.hits-before[0],cache_misses=ctx.audit.misses-before[1]));print(rows[-1],flush=True)
ctx.close();assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,setup_seconds=setup,scope='Fresh full bounded NET-history production in one persistent context. All paths, events, rounds, failures and history equal independently audited original output. Prior complete selections supplied from accepted archives for steps2/3; proof feedback/native production not integrated. No deployment workflow speedup claim.'),indent=2)+'\n')
