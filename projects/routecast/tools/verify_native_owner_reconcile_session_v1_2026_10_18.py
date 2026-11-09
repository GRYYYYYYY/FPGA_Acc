"""Real native path old/new/old owner-session replay on exposed12 targets."""
import json,hashlib,time
from pathlib import Path
from native_owner_reconcile_session_v1 import Session
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths,authenticate
from unified_rr_audit_inventory_v1 import read
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_owner_session_reconcile_v1_2026-10-18';bindings={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for data in iter(lambda:f.read(4*1024*1024),b''):h.update(data)
 return h.hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
def rejected(fn,state):
 old=state.state;generation=state.generation
 try:fn()
 except (ValueError,RuntimeError):pass
 else:raise AssertionError('invalid operation admitted')
 assert state.state is old and state.generation==generation
cases=load(R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json')['cases']
original=load(R/'experiments/retained_seed_session_native_cohort_v3_2026-10-08/verification.json');rows=[];tick=time.perf_counter()
for width in (8,16,32):
 cs=[c for c in cases if c['width']==width];old=load(cs[0]['old']);authenticate(old)
 inv=read(Path(old['inputs']['graph']['path']),old['graph_sha256']);oldroute=Path(old['inputs']['graph']['path']).with_name('design.route');bindings[str(oldroute)]=sha(oldroute)
 oldpaths=mapped_paths(old,oldroute);oldq={q['connection_id']:q for q in old['connections']};session=Session(oldpaths,oldq,inv);initial=dict(session.state.occupancy)
 for c in cs:
  w,i=c['width'],c['index'];target=load(c['target']);authenticate(target);qs={q['connection_id']:q for q in target['connections']}
  out=R/f'experiments/retained_seed_session_native_cohort_v3_2026-10-08/w{w}_m{i}';reference=load(out/'original_budget_verification.json');assert original['bindings'][str(out/'original_budget_verification.json')]==bindings[str(out/'original_budget_verification.json')]
  route=out/'output.route';bindings[str(route)]=sha(route);paths=mapped_paths(target,route)
  generation=session.generation;before=session.state
  ticket,summary=session.prepare(paths,qs,inv,generation=generation)
  assert session.state is before
  missing=dict(paths);missing.pop(next(iter(missing)))
  rejected(lambda:session.prepare(missing,qs,inv,generation=generation),session)
  rejected(lambda:session.prepare(paths,qs,inv,generation=generation+1),session)
  other=Session(oldpaths,oldq,inv);foreign,_=other.prepare(paths,qs,inv,generation=0)
  rejected(lambda:session.commit(foreign,generation=generation),session);other.close()
  # Snapshot must survive caller mutations after preparation.
  cid=next(iter(qs));saved=qs[cid]['source'];qs[cid]['source']=-1
  session.commit(ticket,generation=generation);qs[cid]['source']=saved
  assert session.state.queries[cid]['source']==saved
  assert {str(n):v for n,v in session.state.occupancy.items()}==reference['physical']['node_occupancy']
  rejected(lambda:session.commit(ticket,generation=generation),session)
  dirty={q['net_id'] for cid,q in qs.items() if (q['source'],q['sink'])!=(oldq[cid]['source'],oldq[cid]['sink'])}
  outside=set(summary['changed_nets'])-dirty
  back,_=session.prepare(oldpaths,oldq,inv,generation=session.generation);session.commit(back,generation=session.generation)
  assert dict(session.state.occupancy)==initial and dict(session.state.paths)==oldpaths
  rows.append(dict(width=w,index=i,changed_connections=len(summary['changed_connection_ids']),actual_changed_nets=len(summary['changed_nets']),changed_nets_outside_endpoint_closure=len(outside),forward_full_occupancy_exact=True,rollback_old_full_paths_and_occupancy_exact=True,foreign_stale_missing_and_mutable_input_checks=True))
  print(w,i,'persistent old/new/old PASS',len(outside),'outside endpoint closure',flush=True)
 session.close();rejected(lambda:session.prepare(oldpaths,oldq,inv,generation=session.generation),session)
 for entry in old['inputs'].values():bindings[entry['path']]=entry['sha256']
for name in ['native_owner_reconcile_session_v1.py','verify_native_owner_reconcile_session_v1_2026_10_18.py','actual_change_physical_delta_v1_2026_10_18.py','actual_change_budget_recheck_v1_2026_10_18.py','native_route_ledger_import_compact.py','unified_rr_audit_inventory_v1.py']:
 p=R/'tools'/name;bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,wall_seconds=time.perf_counter()-tick,scope='Internal physical owner-state prepare/commit only; all12 exposed native outputs. Not full route publication, canonical admission, original-budget feasibility, timing gain, graph/RC model integration or unseen validation.'),f,indent=2)
