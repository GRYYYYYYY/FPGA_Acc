"""Authenticated budget repair through the maintained explicit context API."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from budget_repair_engine import repair_budget
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_explicit_budget_engine_v2_2026-10-06';out.mkdir();parent=root/'experiments/ex5p_bounded_history_repair_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert proof['receipt_sha256']==sha(parent/'receipt.json');ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json'
p={'parent_sha256':sha(parent/'receipt.json'),'endpoint_sha256':sha(ep),'sources':{name:sha(root/'tools'/name) for name in ('persistent_rc_context.py','budget_repair_engine.py','native_capacity_rc_search.py')},'repairs_max':4,'budget_ns':1,'max_labels':10000,'policy':'Original budget repair allocation/queue policy; explicit persistent context handles all history and demand updates. Added explicit empty-demand-disconnected terminal status. No native reference paths/timing read.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic();ctx=PersistentRCContext(ep);setup=time.monotonic()-start;start=time.monotonic();r=repair_budget(ctx,prior);querytime=time.monotonic()-start
baseline=json.loads((root/'experiments/ex5p_budget_repair_2026-10-06/receipt.json').read_text());normalized=json.loads(json.dumps(r));mismatches=[k for k in r if normalized[k]!=baseline[k]];assert not mismatches,mismatches
assert ctx.history=={int(n):c for n,c in r['history'].items()}
assert all(c==ctx.rc.increments[s]*(1+ctx.history.get(ctx.rc.fields['dest_ranks'][s],0)) for s,c in enumerate(ctx.native.arrays[3]))
r.update({'parent_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'context_initialization_s':setup,'repair_s':querytime,'algorithmic_parity':True});(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'],r['completed_connections'],'setup',setup,'repair',querytime)
