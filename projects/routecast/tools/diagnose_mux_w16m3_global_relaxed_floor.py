"""All-connection relaxed floor diagnostic; no physical candidate produced."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
from exact_incremental_timing_dag import ExactTimingDAG
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07';p=json.loads((base/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(16,3));file=base/'w16_m3/result.json';d=json.loads(file.read_text());ctx=PersistentRCContext(case['target']);queries=ctx.context[5]
af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w16_m3.json';gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w16_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w16.json';a=json.loads(af.read_text());g=json.loads(gf.read_text());m=json.loads(mf.read_text());out=ROOT/'experiments/mux_w16m3_global_relaxed_floor_2026-10-07';out.mkdir(exist_ok=True);cache={};certificates=[];rows=[];start=time.perf_counter()
for index in (6,8):
 s=d['allocations'][index];floors={};refs={};unsupported=[]
 pair_bans={}
 for q in queries:pair_bans.setdefault((q['source'],q['sink']),set()).update(s['restrictions'].get(str(q['net_id']),[]))
 for q in queries:
  bans=pair_bans[(q['source'],q['sink'])];key=(q['source'],tuple(sorted(bans)))
  if key not in cache:
   cert=shortest_delay(ctx,q['source'],q['sink'],bans);cache[key]=len(certificates);certificates.append(dict(source=q['source'],bans=sorted(bans),distances=cert['distances'],predecessor_slots=cert['predecessor_slots']))
  ci=cache[key];minimum=certificates[ci]['distances'].get(q['sink']);refs[str(q['connection_id'])]=ci
  if minimum is None:unsupported.append(q['connection_id'])
  else:floors[str(q['connection_id'])]=F(minimum*10**9,ctx.rc.scale)
 assert not unsupported
 dag=ExactTimingDAG.from_native_metadata(g,m,a,floors)
 rows.append(dict(allocation=index,minimum_ns={c:str(v) for c,v in floors.items()},certificate_indices=refs,relaxed_cpd_ns=str(dag.cpd),planning_cpd_ns=s['floor_cpd_ns'],target_ns=a['target_cpd_ns'],relaxed_target_pass=dag.cpd<=F(a['target_cpd_ns']),lowered_connections=sum(v<F(s['floor_ns'][c]) for c,v in floors.items())))
 print(index,'global relaxed CPD',float(dag.cpd),'target',a['target_cpd_ns'],'certs',len(cache),flush=True)
(out/'certificates.json').write_text(json.dumps(certificates)+'\n')
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={str(f):sha(f) for f in (file,af,gf,mf,Path(case['target']),out/'certificates.json')},graph_sha256=ctx.endpoint_metadata['graph_sha256'],scale=ctx.rc.scale,rows=rows,seconds=time.perf_counter()-start,scope='All connections relaxed capacities-positive paths, ignoring owner occupancy but preserving actual query pair bans. Shared shortest and forward timing diagnostic; independent proof pending. Relaxed target pass is not simultaneous capacity feasibility/native STA/accepted route or time gain.'),indent=2)+'\n')
