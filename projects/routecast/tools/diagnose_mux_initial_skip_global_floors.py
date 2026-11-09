"""Globally relaxed floor diagnostic for four frozen initial planning skips."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07';protocol=base/'protocol.json';p=json.loads(protocol.read_text());out=ROOT/'experiments/mux_initial_skip_global_floors_2026-10-07';out.mkdir(exist_ok=True);summary=[]
for w,i in ((16,1),(16,2),(32,0),(32,1)):
 case=next(c for c in p['cases'] if (c['width'],c['index'])==(w,i));seed=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json';seed_data=json.loads(seed.read_text());assert seed_data['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED';ctx=PersistentRCContext(case['target']);af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';gf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';a=json.loads(af.read_text());g=json.loads(gf.read_text());m=json.loads(mf.read_text());work=out/f'w{w}_m{i}';work.mkdir(exist_ok=True);certs=[];cache={};floors={};refs={};start=time.perf_counter()
 for q in ctx.context[5]:
  source=q['source']
  if source not in cache:
   cert=shortest_delay(ctx,source,q['sink'],set());cache[source]=len(certs);certs.append(dict(source=source,bans=[],distances=cert['distances'],predecessor_slots=cert['predecessor_slots']))
  ci=cache[source];minimum=certs[ci]['distances'].get(q['sink']);assert minimum is not None;cid=str(q['connection_id']);refs[cid]=ci;floors[cid]=F(minimum*10**9,ctx.rc.scale)
 dag=ExactTimingDAG.from_native_metadata(g,m,a,floors);row=dict(width=w,index=i,allocation=None,minimum_ns={c:str(v) for c,v in floors.items()},certificate_indices=refs,relaxed_cpd_ns=str(dag.cpd),planning_cpd_ns=seed_data['model_floor_cpd_ns'],target_ns=a['target_cpd_ns'],relaxed_target_pass=dag.cpd<=F(a['target_cpd_ns']),lowered_connections=sum(v<F(seed_data['floor_ns'][c]) for c,v in floors.items()))
 cf=work/'certificates.json';cf.write_text(json.dumps(certs)+'\n');receipt=dict(width=w,index=i,source_sha256=sha(Path(__file__)),protocol_sha256=sha(protocol),bindings={str(f):sha(f) for f in (seed,af,gf,mf,Path(case['target']),cf)},graph_sha256=ctx.endpoint_metadata['graph_sha256'],scale=ctx.rc.scale,rows=[row],seconds=time.perf_counter()-start,scope='All connections minimum ignoring occupancy, no bans. Independent shortest/timing verification pending. Old-local-offset model, not simultaneous physical/native timing proof. No policy change or route produced.');(work/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');summary.append(dict(width=w,index=i,relaxed_cpd_ns=str(dag.cpd),target_ns=a['target_cpd_ns'],relaxed_target_pass=row['relaxed_target_pass'],receipt_sha256=sha(work/'receipt.json')));(out/'receipt.json').write_text(json.dumps(dict(rows=summary,complete=len(summary)==4),indent=2)+'\n');print(w,i,float(dag.cpd),'target',float(F(a['target_cpd_ns'])),row['relaxed_target_pass'],flush=True)
