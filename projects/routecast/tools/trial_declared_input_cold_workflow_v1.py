"""Prospective cold routing/physical-budget/canonical boundary with declared caches."""
import json,os,re,shutil,subprocess,time,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_cached import audit
from buffered_rc_node_classes import read
from loaded_native_canonical_reload import canonical_reload
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
E=R/'experiments';D=E/'declared_input_cold_workflow_v1_2026-10-08';D.mkdir(exist_ok=False)
case=next(c for c in json.loads((E/'owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=json.loads(Path(case['target']).read_text());graph=Path(ep['inputs']['graph']['path'])
source=R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128';place=E/'mux_budget_move_cohort_2026-10-06/w32_m2/target.place'
candidate_protocol=E/'old_route_to_native_workflow_v1_2026-10-08/protocol.json'
common=json.loads(candidate_protocol.read_text())['bindings']
common_inputs=[Path(case['old']),Path(case['target']),Path(case['budget']),source/'design.route',source/'design.net',source/'design.blif',place,
 E/'mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json',E/'mux_full_timing_rr_2026-10-06/w32.json',E/'mux_allfanin_budgets_2026-10-06/w32_m2.json']
assert all(common[str(p)]==sha(p) for p in common_inputs)
build=R/'build/native_resume_branch_partial_v8_2026-10-08';br=json.loads((build/'receipt.json').read_text());binary=build/'routecast_resume_vpr';assert sha(binary)==br['binary_sha256']
prior=E/'mux32_old_placement_cold_control_2026-10-07/receipt.json';pr=json.loads(prior.read_text())
cmd=[str(binary),*pr['command'][1:]]
bindings={**closure([Path(__file__)]),str(candidate_protocol):sha(candidate_protocol),str(graph):sha(graph),str(binary):sha(binary),str(build/'receipt.json'):sha(build/'receipt.json'),str(prior):sha(prior)}
bindings.update({str(p):sha(p) for p in common_inputs})
scope='Same supplied original packed netlist, target placement, RR and options as candidate, with supplied old route/endpoints/budget/fixed-local model available to both. Cold does not need old-route/model computations. Frozen graph/compiler/context preparation is outside both declared clocks; cache generation/amortization not proved. Actual cold routing then complete Fraction budget/physical audit, post-routing canonical FULL STA and path audit. Sequential single observations, not paired; original HDL equivalence and full original-input gain unproved.'
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,common_cached_inputs={str(p):sha(p) for p in common_inputs},scope=scope),indent=2)+'\n')
started=time.perf_counter();phases={};tick=started;work=D/'cold';work.mkdir()
for name in ('design.blif','design.net'):shutil.copyfile(source/name,work/name)
shutil.copyfile(place,work/'design.place')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
with (work/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
text=(work/'run.log').read_text();assert code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text and 'ROUTECAST_RESUME_LOADED_TREES' not in text
cpd=F(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);phases['cold_routing_and_setup']=time.perf_counter()-tick;tick=time.perf_counter()
route=work/'output.route';physical=audit(graph,route);assert physical['overflow_units']==0 and physical['all_printed_branch_arc_switch_and_union_checks_pass']
paths={}
for name,branches in physical_paths(route).items():
 for branch in branches:
  key=name,branch[0][0],branch[-1][0];assert key not in paths;paths[key]=branch
ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];budget=json.loads(Path(case['budget']).read_text());rows=[]
assert len(paths)==len(ep['connections'])==1929
for q in ep['connections']:
 cid=q['connection_id'];path=paths[ep['net_names'][str(q['net_id'])],q['source'],q['sink']];nr,nc=classes[ids[q['source']]];delay=nr*nc/2
 for dst,s in path[1:]:nr,nc=classes[ids[dst]];sr,td=switches[s];delay+=(sr+nr/2)*nc+td
 limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']));rows.append(dict(connection_id=cid,delay_seconds=str(delay),budget_ns=str(limit),budget_pass=delay*10**9<=limit))
(D/'fraction_budget_rows.json').write_text(json.dumps(rows,indent=2)+'\n');phases['complete_physical_fraction_budget_audit']=time.perf_counter()-tick;tick=time.perf_counter()
p=dict(width=32,decision='R',command=cmd,cpd_ns=float(cpd),files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
canonical=canonical_reload(p,work,D/'canonical');phases['canonical_reload']=time.perf_counter()-tick;tick=time.perf_counter()
norm=lambda path:Counter((name,branch) for name,branches in physical_paths(path).items() for branch in branches)
assert norm(D/'canonical/design.route')==norm(route)
cp=audit(graph,D/'canonical/design.route');assert cp['overflow_units']==0 and len(cp['connections'])==1929
import xml.etree.ElementTree as ET
length={}
for node in ET.parse(graph).getroot().find('rr_nodes'):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[int(node.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
wire=sum(sum(length.get(n,0) for n in {n for branch in branches for n,s in branch}) for branches in physical_paths(route).values())
assert wire==int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1])
phases['canonical_physical_and_geometry_audit']=time.perf_counter()-tick
assert all(sha(p)==h for p,h in bindings.items())
elapsed=time.perf_counter()-started
report=dict(bindings=bindings,protocol_sha256=sha(D/'protocol.json'),exit_code=code,cold_cpd_ns=str(cpd),wirelength=wire,
 budget_violation_ids=[row['connection_id'] for row in rows if not row['budget_pass']],connections=1929,canonical=canonical,
 phases_seconds=phases,declared_input_workflow_seconds=elapsed,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()},scope=scope)
(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','files','canonical')},flush=True)
