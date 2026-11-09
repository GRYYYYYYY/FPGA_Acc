"""Fresh explicit initial engine, then reset/repeat using the same graph context."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from joint_prediction_engine import predict_joint
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_explicit_joint_engine_2026-10-06';out.mkdir();ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';proof=json.loads((ep.parent/'verification.json').read_text());assert proof['endpoint_sha256']==sha(ep)
p={'endpoint_sha256':sha(ep),'budget_ns':1,'max_labels':10000,'fallback_limit':64,'sources':{name:sha(root/'tools'/name) for name in ('joint_prediction_engine.py','persistent_rc_context.py','native_capacity_rc_search.py')},'policy':'Unchanged NET/connection order, hardcapacity/delaycost/64minimumdelay fallbacks; explicit context from empty state, repeated after reset. No native route/timing input.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(ep);setup=time.monotonic()-start;start=time.monotonic();r=predict_joint(ctx);elapsed=time.monotonic()-start
baseline=json.loads((root/'experiments/nonzero_rc_ex5p_joint_delay_2026-10-06/receipt.json').read_text());normalized=json.loads(json.dumps(r));assert all(normalized[k]==baseline[k] for k in r)
start=time.monotonic();second=predict_joint(ctx);repeat=time.monotonic()-start;assert r==second
r.update({'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'context_initialization_s':setup,'initial_prediction_s':elapsed,'reset_repeat_prediction_s':repeat,'reset_repeat_equal':True,'algorithmic_parity':True});(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'],r['completed_connections'],'setup',setup,'initial',elapsed,'repeat',repeat)
