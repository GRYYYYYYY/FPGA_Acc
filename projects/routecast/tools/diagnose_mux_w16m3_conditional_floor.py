import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
from exact_incremental_timing_dag import ExactTimingDAG
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07';p=json.loads((base/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(16,3));file=base/'w16_m3/result.json';d=json.loads(file.read_text());ctx=PersistentRCContext(case['target']);queries={q['connection_id']:q for q in ctx.context[5]}
af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w16_m3.json';gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w16_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w16.json';a=json.loads(af.read_text());g=json.loads(gf.read_text());m=json.loads(mf.read_text());rows=[];cache={}
for index in (6,8):
 s=d['allocations'][index];floor={cid:F(v) for cid,v in s['floor_ns'].items()};changes={}
 for cid in (352,353,354):
  q=queries[cid];bans=set(s['restrictions'].get(str(q['net_id']),[]));key=(q['source'],tuple(sorted(bans)))
  if key not in cache:cache[key]=shortest_delay(ctx,q['source'],q['sink'],bans)
  cert=cache[key];minimum=cert['distances'].get(q['sink']);assert minimum is not None
  changes[str(cid)]=F(minimum*10**9,ctx.rc.scale)
 dag=ExactTimingDAG.from_native_metadata(g,m,a,floor);assert dag.cpd==F(s['floor_cpd_ns'])
 rows.append(dict(allocation=index,old_floor_cpd_ns=str(dag.cpd),replacement_cpd_ns=str(dag.update(changes)),connections=[dict(connection_id=int(cid),old_floor_ns=str(floor[cid]),relaxed_minimum_ns=str(v)) for cid,v in changes.items()],target_ns=a['target_cpd_ns']))
out=ROOT/'experiments/mux_w16m3_conditional_floor_diagnosis_2026-10-07';out.mkdir(exist_ok=True);(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={str(f):sha(f) for f in (file,af,gf,mf,Path(case['target']))},rows=rows,scope='Diagnostic exact integer shortest solver and forward DAG; independent shortest and backward timing verification pending. Replaces only newly expanded retained CIDs352-354, not all repair-releasable retained paths. No prospective route or infeasibility proof.'),indent=2)+'\n');print(rows,flush=True)
