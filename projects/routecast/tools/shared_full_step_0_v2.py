"""Actual full4 branchpartial native reload/resume; preserve all failures and path changes."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from fractions import Fraction as F
from native_route_ledger_import_compact import physical_paths
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'adder_multinet_wire_guard_shared_serialization_v2_2026-10-08';D=E/'adder_wire_guard_matched_cold_v7_2026-10-08';D.mkdir(exist_ok=False)
v=json.loads((S/'verification.json').read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings={**v['bindings'],str(S/'verification.json'):sha(S/'verification.json')}
binary=R/'build/native_resume_branch_partial_v8_2026-10-08/routecast_resume_vpr';br=binary.parent/'receipt.json';assert sha(binary)==json.loads(br.read_text())['binary_sha256'];arch=Path(json.loads((E/'adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits_command.json').read_text())['command'][1]);bindings[str(binary)]=sha(binary);bindings[str(arch)]=sha(arch);bindings[str(Path(__file__))]=sha(Path(__file__))
plans=[]
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';m=json.loads(ep.read_text());g=Path(m['inputs']['graph']['path']);seed=S/f'step_{step}.route';bp=E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json'
 cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(g),'--route_chan_width','300','--num_workers','1','--check_route','full','--max_router_iterations','100','--seed','1']
 plans.append(dict(step=step,endpoints=str(ep),seed=str(seed),budget=str(bp),command=cmd));bindings[str(ep)]=sha(ep);bindings[str(bp)]=sha(bp);bindings[str(g.with_name('design.blif'))]=sha(g.with_name('design.blif'))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,plans=plans),indent=2)+'\n');rows=[];inv=None;start=time.perf_counter()
for p in plans:
 step=p['step'];m=json.loads(Path(p['endpoints']).read_text());g=Path(m['inputs']['graph']['path']);w=D/f'step_{step}';w.mkdir()
 for name in ('design.blif','design.net'):shutil.copyfile(g.with_name(name),w/name)
 shutil.copyfile(m['inputs']['place']['path'],w/'design.place');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 with (w/'run.log').open('x') as log:code=subprocess.run(p['command'],cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 text=(w/'run.log').read_text();row=dict(step=step,exit_code=code,loaded='ROUTECAST_RESUME_LOADED_TREES' in text,full_check='Completed routing consistency check successfully.' in text,vpr_succeeded='VPR succeeded' in text)
 if code==0 and row['full_check']:
  if inv is None:inv=read(g,m['graph_sha256'])
  state,delays,proof=load(w/'output.route',m,inv);budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads(Path(p['budget']).read_text())};fails=sorted(x['connection_id'] for x in delays if F(x['delay_seconds'])>budgets[x['connection_id']]);row.update(connections=len(delays),violation_ids=fails,paths_preserved=physical_paths(w/'output.route')==physical_paths(p['seed']),cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]));(w/'audit.json').write_text(json.dumps(dict(rows=delays,physical=proof,violation_ids=fails),indent=2)+'\n')
 for f in w.iterdir():
  if f.is_file():bindings[str(f)]=sha(f)
 rows.append(row);print(row,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Actual4 v8 seeded FULL routing and complete physical/exactbudget audits. Route paths may change; not canonical independent packedpin reload/HDL or fullworkflow gain.'),indent=2)+'\n')
