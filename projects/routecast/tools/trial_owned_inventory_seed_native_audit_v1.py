"""Cold direct seed sessions, actual native resume, same-owned-inventory full audits."""
import json,os,re,shutil,subprocess,sys,time
from fractions import Fraction as F
from pathlib import Path
from retained_seed_session_direct_v1 import RetainedSeedSession
from direct_retained_route_import_v1 import load
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
D=R/'experiments/owned_inventory_seed_native_audit_v1_2026-10-08';D.mkdir(exist_ok=False)
p=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=sorted(json.loads(p.read_text())['cases'],key=lambda c:(c['width'],c['index']))
template=json.loads((R/'experiments/mux32_old_placement_cold_control_2026-10-07/receipt.json').read_text())['command']
binary=R/'build/native_resume_branch_partial_v8_2026-10-08/routecast_resume_vpr'
bindings={**closure([Path(__file__)]),str(p):sha(p),str(binary):sha(binary),str(Path(template[1])):sha(template[1])}
for c in cases:
 for k in ('old','target','budget'):bindings[c[k]]=sha(c[k])
 for ep in (c['old'],c['target']):
  meta=json.loads(Path(ep).read_text());bindings.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
 g=Path(meta['inputs']['graph']['path']);bindings[str(g.with_name('design.route'))]=sha(g.with_name('design.route'));bindings[str(g.with_name('design.blif'))]=sha(g.with_name('design.blif'))
assert all(sha(f)==h for f,h in bindings.items())
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='All12 provided-input targets, cold3 inventory/direct oldimports, fresh seed/native/fullphysical/originalbudget audit in one parent. Shared immutable inventory; no advancing accepted route epoch. Initial protocol and final receipt/verifier outside; supplied input generation excluded.'),indent=2)+'\n')
start=time.perf_counter();rows=[];sessions={}
for c in cases:
 w=c['width'];i=c['index'];phases={};tick=time.perf_counter()
 if w not in sessions:
  old=json.loads(Path(c['old']).read_text());g=Path(old['inputs']['graph']['path']);sessions[w]=RetainedSeedSession(c['old'],g.with_name('design.route'))
 session=sessions[w];assert sha(c['old'])==sha(session.endpoint)
 phases['setup_seconds']=time.perf_counter()-tick;tick=time.perf_counter()
 seed=session.write_seed(c['target'],c['budget'],D/f'w{w}_m{i}_seed');phases['seed_seconds']=time.perf_counter()-tick;tick=time.perf_counter()
 target=json.loads(Path(c['target']).read_text());budget=json.loads(Path(c['budget']).read_text());g=Path(target['inputs']['graph']['path']);out=D/f'w{w}_m{i}';out.mkdir()
 for name in ('design.net','design.blif'):shutil.copyfile(g.with_name(name),out/name)
 shutil.copyfile(target['inputs']['place']['path'],out/'design.place')
 cmd=[str(binary),*template[1:]];cmd[cmd.index('--read_rr_graph')+1]=str(g)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=seed['route'],ROUTECAST_RESUME_ALLOW_PARTIAL='1',ROUTECAST_RESUME_ALLOW_BRANCH_PARTIAL='1')
 with (out/'run.log').open('x') as log:code=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 text=(out/'run.log').read_text();assert code==0 and all(s in text for s in ('ROUTECAST_RESUME_LOADED_TREES','Completed routing consistency check successfully.','VPR succeeded'))
 nativefiles={str(f):sha(f) for f in out.iterdir() if f.is_file()};phases['native_seconds']=time.perf_counter()-tick;tick=time.perf_counter()
 state,delays,proof=load(out/'output.route',target,session.inventory);fail=[];budgetrows=[]
 for x in delays:
  cid=x['connection_id'];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']));ok=F(x['delay_seconds'])*10**9<=limit
  budgetrows.append(dict(connection_id=cid,delay_seconds=x['delay_seconds'],budget_ns=str(limit),budget_pass=ok))
  if not ok:fail.append(cid)
 audit=out/'original_budget_verification.json';audit.write_text(json.dumps(dict(rows=sorted(budgetrows,key=lambda x:x['connection_id']),physical=proof,violation_ids=sorted(fail)),indent=2)+'\n')
 phases['audit_seconds']=time.perf_counter()-tick
 bindings.update(seed['forest']['bindings']);bindings[seed['route']]=sha(seed['route']);bindings[str(Path(seed['route']).with_name('forest.json'))]=sha(Path(seed['route']).with_name('forest.json'));bindings.update(nativefiles);bindings[str(audit)]=sha(audit)
 row=dict(width=w,index=i,command=cmd,connections=len(delays),violation_ids=sorted(fail),cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),phases=phases);rows.append(row)
 (D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(w,i,'full audit',len(delays),'violations',len(fail),flush=True)
assert len(rows)==12 and all(sha(f)==h for f,h in bindings.items())
elapsed=time.perf_counter()-start
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,protocol_sha256=sha(D/'protocol.json'),declared_component_seconds=elapsed,cold_inventory_builds=3,original_budget_admitted_cases=sum(not r['violation_ids'] for r in rows),full_original_input_workflow_seconds=None,scope='Measured one-parent declared-input seed/native/audit component; includes cold shared inventory, output/progress/hash closure. External seed proofs and independent audit verifier not timed; no cold arm or gain claim.'),indent=2)+'\n');print('TERMINAL component',elapsed)
