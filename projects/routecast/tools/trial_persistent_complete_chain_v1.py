"""Fresh history plus proof feedback chain in one persistent context; native pending."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from persistent_route_context_v1 import RouteContext
from persistent_net_history_v1 import generate
from persistent_proof_feedback_v1 import select
from independent_route_cnf_structure_v1 import verify_encoding
from verify_certified_cnf_dependency_cdcl_v1 import verify
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'persistent_complete_chain_v1_2026-10-09';D.mkdir(exist_ok=False);bindings=closure([Path(__file__)])
base=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';ctx=RouteContext(base);bindings[str(base)]=sha(base);bindings[str(ctx.graph)]=ctx.digest;bindings.update(ctx.search.bindings)
op=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_0_state.json';bindings[str(op)]=sha(op);old={int(cid):path for cid,path in json.loads(op.read_text())['state'].items()};rows=[]
for step,prefix in enumerate(('fresh_history_workflow_v1','history_step2_v1','history_step3_v1'),1):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json';q=ctx.endpoints(ep);budgets={row['connection_id']:F(*row['exact_delay_s']) for row in json.loads(bp.read_text())}
 tick=time.perf_counter();history=generate(ctx,q,budgets,old);result=select(ctx,q,budgets,old,history);seconds=time.perf_counter()-tick
 assert result['result']['status']=='SAT' and len(result['paths'])==516
 # Independent structural/proof replay for every actual candidate prefix.
 for row in result['rounds']:
  prefixbank={cid:[option for option in opts if not isinstance(option['origin'],dict) or option['origin']['iteration']<row['iteration']] for cid,opts in result['bank'].items()}
  verify_encoding(row['encoding'],prefixbank,q,ctx.audit.inventory);verify(row['encoding']['clauses'],row['result'])
 out=D/f'step_{step}_result.json';out.write_text(json.dumps(result,indent=2)+'\n');hp=D/f'step_{step}_history.json';hp.write_text(json.dumps(history,indent=2)+'\n')
 oracle=E/f'{prefix}_stage_2_2026-10-09/result.json';assert json.loads(out.read_text())==json.loads(oracle.read_text())
 authority=oracle.with_name('independent_verification.json');doc=json.loads(authority.read_text());assert all(sha(p)==h for p,h in doc['bindings'].items())
 for p in (ep,bp,out,hp,oracle,authority):bindings[str(p)]=sha(p)
 old=result['paths'] # Next production input is this run's actual selected state.
 rows.append(dict(step=step,connections=len(old),rounds=len(result['rounds']),bank_candidates=sum(map(len,result['bank'].values())),all_result_equals_authenticated_original=True,history_feedback_component_seconds=seconds));print(rows[-1],flush=True)
ctx.close();assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Fresh given step0 then own actual step1/2 selections drive next production; one persistent context. All encoding/proof/model/path outputs exactly equal independently audited original and per-round structural/naive proof replay performed. No native/canonical fresh runs or actual sameStore commits here; component timer excludes setup/oracle/audit/archive and no total speedup claim.'),indent=2)+'\n')
