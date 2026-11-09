"""Real subprocess validation rejection, old-state reload and candidate publication."""
import json,os,re,shutil,subprocess,time,resource
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from transaction_shared_tree_ledger_v1 import TransactionLedger
from staged_place_route_transaction_v1 import PlaceRouteStore
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_native_seed_recovery_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter()
FROOT=E/'adder_legal_route_budget_fixture_v1_2026-10-09';H=E/'adder_cross_place_retention_v3_2026-10-09';S=E/'adder_cross_place_hybrid_serialization_v1_2026-10-09';P=E/'adder_cross_place_hybrid_native_v1_2026-10-09/protocol.json';V=E/'adder_cross_place_hybrid_quality_v2_2026-10-09/verification.json'
v=json.loads(V.read_text());bindings={**v['bindings'],str(V):sha(V),str(P):sha(P),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());fixtures=json.loads((FROOT/'receipt.json').read_text())['plans'];plans=json.loads(P.read_text())['plans'];g,digest,nodes,fields,rc,_=load_endpoints(fixtures[0]['endpoints']);inv=read(g,digest);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
class NativeRejected(RuntimeError):pass
def signature(t):
 normalize=lambda o:{k:dict(v) for k,v in o.items() if v}
 return (t.state,t.queries,normalize(t.nodes),normalize(t.parents),normalize(t.parent_uses),dict(t.occupancy),dict(t.wire))
def run(step,phase,ep,seed,command,budget):
 assert all(sha(p)==h for p,h in bindings.items());meta=json.loads(Path(ep).read_text());w=D/f'step_{step}_{phase}';w.mkdir()
 for name in ('design.blif','design.net'):shutil.copyfile(g.with_name(name),w/name)
 shutil.copyfile(meta['inputs']['place']['path'],w/'design.place');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESUME_SAME_PLACE_ROUTE=str(seed),ROUTECAST_RESUME_ALLOW_PARTIAL='1',ROUTECAST_RESUME_ALLOW_BRANCH_PARTIAL='1')
 (w/'command.json').write_text(json.dumps(dict(command=command,endpoints=str(ep),seed=str(seed),budget=str(budget)),indent=2)+'\n')
 with (w/'run.log').open('x') as log:code=subprocess.run(command,cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
 text=(w/'run.log').read_text();row=dict(phase=phase,exit_code=code,full_check='Completed routing consistency check successfully.' in text,loaded='ROUTECAST_RESUME_LOADED_TREES' in text)
 state=None
 if code==0:
  assert row['full_check'] and row['loaded'] and 'VPR succeeded' in text
  state,delays,proof=load(w/'output.route',meta,inv);budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(Path(budget).read_text())};assert len(delays)==516 and all(F(x['delay_seconds'])<=budgets[x['connection_id']] for x in delays)
  paths=lambda p:Counter((name,path) for name,ps in __import__('native_route_ledger_import_compact').physical_paths(p).items() for path in ps)
  assert paths(w/'output.route')==paths(seed);row.update(connections=516,model_budget_pass=True,paths_equal=True,cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])
 for file in w.iterdir():
  if file.is_file():bindings[str(file)]=sha(file)
 return row,state
rows=[]
for plan in plans:
 step=plan['step'];old=fixtures[step-1];oq={q['connection_id']:q for q in json.loads(Path(old['endpoints']).read_text())['connections']};tq={q['connection_id']:q for q in json.loads(Path(plan['endpoints']).read_text())['connections']};oldstate={int(c):p for c,p in json.loads(Path(old['state']).read_text())['state'].items()};target={int(c):p for c,p in json.loads((H/f'step_{step}_hybrid_state.json').read_text()).items()};nets=set(json.loads((H/'verification.json').read_text())['rows'][step-1]['closure_iterations'][-1]['replaced_nets']);replacements={c:p for c,p in target.items() if tq[c]['net_id'] in nets};store=PlaceRouteStore(TransactionLedger(oldstate,oq,fields['capacities'],length));before=signature(store.snapshot()[1]);staged=store.stage(tq,replacements);events=[]
 corrupt=D/f'step_{step}_corrupt.route';original=Path(plan['seed']).read_text();mutated,count=re.subn(r'(SINK[^\n]*Net_pin_index:\s*)\d+',r'\g<1>2147483647',original,count=1);assert count==1 and mutated!=original;corrupt.write_text(mutated);bindings[str(corrupt)]=sha(corrupt);bad=list(plan['command'])
 def reject(candidate):
  row,_=run(step,'reject',plan['endpoints'],corrupt,bad,plan['budget']);events.append(row)
  if row['exit_code']==0:raise AssertionError('corrupted seed accepted')
  raise NativeRejected('native seed rejection')
 try:store.commit(staged,reject)
 except NativeRejected:pass
 else:raise AssertionError('rejected candidate published')
 assert store.snapshot()[0]==0 and signature(store.snapshot()[1])==before
 recovery,reloaded=run(step,'recover_old',old['endpoints'],old['witness_route'],plan['command'],old['budgets']);events.append(recovery);assert reloaded==store.snapshot()[1].state
 def accept(candidate):
  row,reloaded=run(step,'accept',plan['endpoints'],plan['seed'],plan['command'],plan['budget']);events.append(row);assert candidate.state==reloaded
 store.commit(staged,accept);assert store.snapshot()[0]==1 and store.snapshot()[1].state=={c:tuple(tuple(x) for x in p) for c,p in target.items()}
 row=dict(step=step,events=events,rejection_epoch_and_state_unchanged=True,old_native_reload_equal=True,success_epoch=1,success_matches_native_output=True);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Actual subprocess corrupted sink-pin seed rejection gate, independent old-state native reload, successful candidate native validation and in-memory publication. Failure injected in seed sink-pin identity before iterative routing; not VPR internal rollback, native mid-route failure, durable placement publication, canonical rerun, online search or speedup. Positive-control budgets.'),indent=2)+'\n')
