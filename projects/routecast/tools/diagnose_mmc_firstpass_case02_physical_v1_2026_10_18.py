import sys,json,traceback
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
D=R/'experiments/mmc_firstpass_case02_physical_diagnostic_v1_2026-10-18';D.mkdir();W=R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18/case_02/on';epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_02/demand/endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);route=W/'output.route';bindings={str(p):sha(p) for p in [Path(__file__).resolve(),epfile,graph,route,W/'native.log',W/'terminal.json']}
try:
 a=audit(graph,route)
 with (D/'physical_audit.json').open('x') as f:json.dump(a,f)
 names={int(m[1]):m[2] for line in route.read_text().splitlines() if (m:=NET.match(line))};known=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in known);required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);missing=required-observed;extra=observed-required
 result=dict(status='diagnostic_complete',bindings=bindings,required_queries=sum(required.values()),observed_queries=sum(observed.values()),overflow_units=a['overflow_units'],missing=list(missing.items()),extra=list(extra.items()),physical_audit_flags={k:v for k,v in a.items() if isinstance(v,bool)})
except Exception as e:
 result=dict(status='audit_exception',bindings=bindings,error=repr(e),traceback=traceback.format_exc())
with (D/'diagnosis.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps(result),flush=True)
