"""Independent cold native/canonical exact budget and input identity gate."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from native_route_ledger_import_compact import physical_paths
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';N=E/'paired_optimized_chain_v1_arm2_step2_native_v1_2026-10-09';C=E/'paired_optimized_chain_v1_arm2_step2_canonical_v1_2026-10-09';D=E/'paired_optimized_chain_v1_arm2_step2_quality_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter()
nr=json.loads((N/'receipt.json').read_text());cr=json.loads((C/'receipt.json').read_text());protocol=json.loads((N/'protocol.json').read_text());assert len(protocol['plans'])==len(nr['rows'])==len(cr['rows'])==1
bindings={**nr['bindings'],**cr['bindings'],**closure([Path(__file__)])}
for p in (N/'receipt.json',N/'protocol.json',C/'receipt.json'):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());plan=protocol['plans'][0];n=nr['rows'][0];c=cr['rows'][0];assert plan['step']==n['step']==c['step']==2
assert 'seed' not in plan and n['loaded'] is False and n['exit_code']==0 and n['full_check'] and n['vpr_succeeded'] and not n['violation_ids']
assert c['exit_code']==0 and c['mismatches']==c['fixups']==0 and c['original_zero_counter_gate_pass'] and c['semantic_consistency_gate_pass']
ep=Path(plan['endpoints']);meta=json.loads(ep.read_text());g=Path(meta['inputs']['graph']['path']);inv=read(g,meta['graph_sha256']);budgetp=Path(plan['budget']);budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(budgetp.read_text())}
for name,src in [('design.blif',g.with_name('design.blif')),('design.net',g.with_name('design.net')),('design.place',Path(meta['inputs']['place']['path']))]:
 assert sha(src)==sha(N/'step_2'/name);bindings[str(src)]=sha(src)
counts=[];states=[]
for route in (N/'step_2/output.route',C/'step_2/design.route'):
 state,delays,proof=load(route,meta,inv);assert len(delays)==516 and {x['connection_id'] for x in delays}==set(budgets);assert all(F(x['delay_seconds'])<=budgets[x['connection_id']] for x in delays);counts.append(len(delays));states.append(state)
assert states[0]==states[1]
def paths(route):return Counter((name,path) for name,ps in physical_paths(route).items() for path in ps)
assert paths(N/'step_2/output.route')==paths(C/'step_2/design.route');assert float(n['cpd_ns'])==float(c['cpd_ns'])==4.87739 and n['wirelength']==2677
for p in (ep,g,budgetp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,step=2,native_and_canonical_connections=counts,exact_model_budget_pass=True,canonical_zero_counters=True,full_named_paths_preserved=True,input_bytes_authenticated=True,seed_loaded=False,cpd_ns=float(c['cpd_ns']),wirelength=n['wirelength'],native_component_seconds=nr['component_seconds'],canonical_component_seconds=cr['component_seconds'],verification_seconds=time.perf_counter()-start,scope='One actual cold routing quality control with same graph/net/place/budgets/native binary and canonical gates as online step3. Separate component clocks, not unified paired workflow measurement; provided input/budget/build production excluded. No speedup or independent timing target claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
