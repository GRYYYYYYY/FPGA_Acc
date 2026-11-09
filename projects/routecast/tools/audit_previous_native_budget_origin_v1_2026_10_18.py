"""Replay original budget arithmetic and measure old-state violations."""
import json,hashlib,time
from fractions import Fraction as F
from pathlib import Path
from retained_route_session_v2 import RetainedRouteSession
R=Path(__file__).resolve().parents[1];D=R/'experiments/previous_native_budget_origin_v1_2026-10-18';D.mkdir(exist_ok=False)
bindings={}
def load(p):
 p=Path(p);raw=p.read_bytes();bindings[str(p)]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
p=load(R/'experiments/mux_connection_budgets_2026-10-06/protocol.json')
source=R/'tools/prepare_mux_connection_budgets.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==p['source_sha256']
bindings[str(source)]=p['source_sha256']
for f,h in p['bindings'].items():
 assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h,f
 bindings[f]=h
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases']
rows=[]
for width in (8,16,32):
 c=next(c for c in cases if c['width']==width);budget=load(c['budget']);expected={}
 for x in budget['constraints']:
  value=min(F(1),F(x['old_rr_ns'])+F(x['guarded_path_headroom_ns'])/x['external_connections_on_path'])
  assert value==F(x['budget_ns'])
  cid=str(x['connection_id']);expected[cid]=min(expected.get(cid,F(1)),value)
 assert expected=={cid:F(v) for cid,v in budget['budgets_ns'].items()}
 assert F(budget['default_budget_ns'])==1
 ep=load(c['old']);route=Path(ep['inputs']['graph']['path']).with_name('design.route')
 tick=time.perf_counter();session=RetainedRouteSession(c['old'],route)
 violations=[]
 for cid,(delay,edges) in session._rows.items():
  value=F(delay*10**9,session.scale);limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))
  if value>limit:violations.append(dict(connection_id=cid,delay_ns=str(value),budget_ns=str(limit),explicit_budget=str(cid) in budget['budgets_ns']))
 bindings.update(session.bindings)
 rows.append(dict(width=width,connections=len(session._rows),constraints_replayed=len(budget['constraints']),explicit_budget_connections=len(expected),old_state_budget_violations=violations,import_and_accounting_seconds=time.perf_counter()-tick))
 print(width,'old budget violations',len(violations),flush=True)
bindings[str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
report=dict(bindings=bindings,rows=rows,original_budget_arithmetic_exact=True,policy='Old native CPD minus rounded reported path arrival plus 0.001 ns guard, equally shared among external connections; min across reported paths and cap 1 ns; unreported connections default 1 ns. Not the newer floor-derived proxy budget and not a safe global STA bound.',cost_boundary='Old route/timing/canonical identity/RC sample generation and budget extraction are prior-state preparation, not free candidate computation. Cold/shared initialization must be reported symmetrically and update-dependent work paid in each arm.',scope='Fresh import and original-budget arithmetic replay. Existing import supplies physical path and integer RC validation; no new independent XML/canonical verifier, original HDL equivalence or end-to-end timing claim.')
with (D/'verification.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
