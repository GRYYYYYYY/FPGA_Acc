"""Fresh four-stage candidate from endpoint inputs with one explicit context."""
import json,time,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from joint_prediction_engine import predict_joint
from frontier_repair_engine import repair_frontier,repair_history
from budget_repair_engine import repair_budget
from route_ledger_state import RouteLedgerState
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_shared_ledger_engine_2026-10-06';out.mkdir();ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';names=['nonzero_rc_ex5p_joint_delay','ex5p_frontier_repair','ex5p_bounded_history_repair','ex5p_budget_repair'];folders={name:'experiments/ex5p_shared_ledger_engine_2026-10-06/'+str(i) for i,name in enumerate(names)}
p={'endpoint_sha256':sha(ep),'sources':{n:sha(root/'tools'/n) for n in ('persistent_rc_context.py','joint_prediction_engine.py','frontier_repair_engine.py','budget_repair_engine.py','route_ledger_state.py')},'policy':'Original four development stages, one explicit context; candidate generation reads only pre-route endpoints/graph/NET/place. Archived outputs read afterwards for parity only. Stage ledgers reconstructed in memory, no production transaction claim.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(ep);state=RouteLedgerState(ctx);setup=time.monotonic()-start;rows=[];prior=None
for i,fn in enumerate((predict_joint,repair_frontier,repair_history,repair_budget)):
 start=time.monotonic();r=fn(ctx,state=state) if i==0 else fn(ctx,prior,state=state);elapsed=time.monotonic()-start;folder=out/str(i);folder.mkdir();(folder/'protocol.json').write_text(json.dumps({'endpoint_sha256':sha(ep),'stage':names[i]}));r.update({'protocol_sha256':sha(folder/'protocol.json'),'source_sha256':sha(Path(__file__))})
 if i:r['parent_sha256']=sha(out/str(i-1)/'receipt.json')
 (folder/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');prior=r;rows.append({'stage':names[i],'workflow_s':elapsed})
# Adapt independent existing XML audits to the new generated chain, preserving their logic.
for i,name in enumerate(names):
 source=(root/'tools'/('verify_'+name+'.py')).read_text()
 for old,new in folders.items():source=source.replace('experiments/'+old+'_2026-10-06',new)
 source=source.replace('tools/trial_'+name+'.py','tools/trial_ex5p_shared_ledger_engine.py');verifier=out/('audit_'+str(i)+'.py')
 # Generated audit file lives under experiments; force its original workspace root.
 source=source.replace('root=Path(__file__).resolve().parents[1]','root=Path('+repr(str(root))+')');verifier.write_text('import sys\nsys.path.insert(0,'+repr(str(root/'tools'))+')\n'+source)
 code=subprocess.run([sys.executable,str(verifier)],cwd=root).returncode;assert code==0
 actual=json.loads((out/str(i)/'receipt.json').read_text());baseline=json.loads((root/'experiments'/(name+'_2026-10-06')/'receipt.json').read_text());keys=[k for k in baseline if not k.endswith('_sha256') and not k.endswith('_seconds')];assert all(actual[k]==baseline[k] for k in keys),name
 rows[i]['receipt_sha256']=sha(out/str(i)/'receipt.json');rows[i]['verification_sha256']=sha(out/str(i)/'verification.json')
result={'stages':rows,'context_initialization_s':setup,'workflow_s':setup+sum(x['workflow_s'] for x in rows),'complete_connections':prior['completed_connections'],'shared_ledger':True,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
