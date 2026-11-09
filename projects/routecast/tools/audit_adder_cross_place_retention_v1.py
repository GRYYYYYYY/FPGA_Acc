"""Measure endpoint-only reuse against independently certified legal target witnesses."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_legal_route_budget_fixture_v1_2026-10-09';D=E/'adder_cross_place_retention_v1_2026-10-09';D.mkdir(exist_ok=False)
start=time.perf_counter();receipt=json.loads((B/'receipt.json').read_text());v=B/'verification.json';report=json.loads(v.read_text());bindings={**receipt['bindings'],**report['bindings'],str(v):sha(v),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items())
plans=receipt['plans'];metas=[json.loads(Path(p['endpoints']).read_text()) for p in plans];states=[{int(cid):tuple(tuple(x) for x in path) for cid,path in json.loads(Path(p['state']).read_text())['state'].items()} for p in plans]
g=Path(metas[0]['inputs']['graph']['path']);inv=read(g,metas[0]['graph_sha256']);print(type(inv),flush=True)
# Original XML inventory format is inspected explicitly below.
print(list(inv.keys()) if isinstance(inv,dict) else list(vars(inv)),flush=True)
