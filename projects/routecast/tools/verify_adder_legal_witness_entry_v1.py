"""Independent physical/Fraction audit of positive-control actual entry outputs."""
import json,time
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];E=R/'experiments';N=E/'adder_legal_witness_native_entry_v1_2026-10-09';C=E/'adder_legal_witness_canonical_entry_v1_2026-10-09';D=E/'adder_legal_witness_entry_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
start=time.perf_counter();nr=json.loads((N/'receipt.json').read_text());cr=json.loads((C/'receipt.json').read_text());plans=json.loads((N/'protocol.json').read_text())['plans'];bindings={**nr['bindings'],**cr['bindings']}
for p in (N/'receipt.json',N/'protocol.json',N/'decisions.json',C/'receipt.json',Path(__file__)):
 bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
rows=[];inv=None
for p,n,c in zip(plans,nr['rows'],cr['rows']):
 step=p['step'];assert step==n['step']==c['step'];assert n['loaded'] and n['full_check'] and n['vpr_succeeded'] and n['exit_code']==0
 assert c['exit_code']==0 and c['mismatches']==0 and c['fixups']==0 and c['original_zero_counter_gate_pass'] and c['semantic_consistency_gate_pass']
 m=json.loads(Path(p['endpoints']).read_text());g=Path(m['inputs']['graph']['path'])
 if inv is None:inv=read(g,m['graph_sha256'])
 budgets={q['connection_id']:Fraction(*q['exact_delay_s']) for q in json.loads(Path(p['budget']).read_text())}
 counts=[]
 for route in (N/f'step_{step}/output.route',C/f'step_{step}/design.route'):
  state,delays,proof=load(route,m,inv);assert len(delays)==516 and {q['connection_id'] for q in delays}==set(budgets)
  assert all(Fraction(q['delay_seconds'])==budgets[q['connection_id']] for q in delays)
  paths=lambda f:Counter((name,path) for name,ps in physical_paths(f).items() for path in ps)
  assert paths(route)==paths(p['seed']);counts.append(len(delays))
 assert float(n['cpd_ns'])==float(c['cpd_ns'])
 rows.append(dict(step=step,native_and_canonical_connections=counts,exact_model_budget_equality=True,full_named_paths_preserved=True,canonical_zero_counters=True,cpd_ns=float(c['cpd_ns'])))
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,rows=rows,native_entry_seconds=nr['component_seconds'],canonical_seconds=cr['component_seconds'],verification_seconds=time.perf_counter()-start,scope='Actual positive-control witness entry and independent output audit. Component sum excludes witness creation, process startup between commands and final receipt verification; no end-to-end speedup or independent timing target claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
