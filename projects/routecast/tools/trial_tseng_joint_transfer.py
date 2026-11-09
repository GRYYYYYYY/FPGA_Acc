"""Frozen transfer of maintained joint policy; no native route input."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from joint_prediction_engine import predict_joint
from route_ledger_state import RouteLedgerState
root=Path(__file__).resolve().parents[1]
out=root/'experiments/tseng_joint_transfer_2026-10-06';out.mkdir()
ep=root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json'
sources=['trial_tseng_joint_transfer.py','joint_prediction_engine.py','persistent_rc_context.py','route_ledger_state.py','native_capacity_rc_search.py','nonzero_rc_endpoint_context.py']
p={'endpoint_sha256':sha(ep),'sources':{s:sha(root/'tools'/s) for s in sources},'policy':{'max_labels':10000,'fallback_limit':64,'branch_budget_ns':1,'order':'net_id,connection_id','cost':'exact integer buffered RC delay times other NET demand plus one','capacity':'hard other-NET node capacity','tree':'single parent'},'scope':'New same-architecture tseng development transfer; no family independence certificate. No native paths/timing labels passed to generator; retain all failures; no outcome-based parameter changes.'}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
t=time.monotonic();ctx=PersistentRCContext(ep);state=RouteLedgerState(ctx);setup=time.monotonic()-t
t=time.monotonic();r=predict_joint(ctx,max_labels=10000,fallback_limit=64,state=state);wall=time.monotonic()-t
r.update(protocol_sha256=sha(out/'protocol.json'),source_sha256=sha(Path(__file__)),context_setup_s=setup,search_s=wall)
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(r['status'],r['completed_connections'],r['required_connections'],r['failure'],setup,wall)
