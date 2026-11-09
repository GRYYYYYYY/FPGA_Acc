"""Development replay of DAG screen against published old MUX routes."""
import json
from pathlib import Path
from fractions import Fraction as F
from live_state_dag_screen import LiveStateDAGScreen
from pre_route_endpoints import sha
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_cold_actual_timing_model_2026-10-07'
rp=base/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
out=ROOT/'experiments/live_state_dag_screen_replay_2026-10-07';out.mkdir(exist_ok=True)
sources=closure([Path(__file__)]);rows=[]
for row in r['rows']:
 w,i=row['width'],row['index']
 gf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json'
 sf=ROOT/f'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w{w}_m{i}_0/accepted_state.json'
 g=json.loads(gf.read_text());m=json.loads(mf.read_text());a=json.loads(af.read_text());s=json.loads(sf.read_text())
 old={};edges=[]
 for eid,e in g['edges'].items():
  if e['disabled']:continue
  c=a['edge_connection_ids'].get(eid);c=None if c is None else str(c)
  offset=F(m['external_edges'][eid]['old_local_offset_seconds'] if c is not None else e['max_delay_seconds'])*10**9
  edges.append((e['source'],e['sink'],offset,c))
  if c is not None:
   value=F(m['external_edges'][eid]['branch']['rr_delay_seconds'])*10**9
   assert c not in old or old[c]==value
   old[c]=value
 new={str(q['connection_id']):F(q['answer']['delay']*10**9,s['scale']) for q in s['records']}
 # Timing-only replay: neutral wire values isolate this component, not joint QoR admission.
 gate=LiveStateDAGScreen([int(n) for n in g['nodes']],edges,[int(n) for n,k in g['nodes'].items() if k=='SINK'],old,0)
 decision=gate.trial(new,0,complete=True)
 assert F(decision['candidate_model_cpd_ns'])==F(row['actual_model_cpd_ns'])
 assert gate.trial(old,0,complete=True)['model_admitted']
 rows.append(dict(width=w,index=i,decision=decision,inputs={str(p):sha(p) for p in (gf,mf,af,sf)}))
assert all(sha(p)==h for p,h in sources.items())
(out/'receipt.json').write_text(json.dumps(dict(sources=sources,parent_sha256=sha(rp),rows=rows,scope='Retrospective DEVELOPMENT timing-only replay, wire neutral zero. Published old full DAG versus archived moved cold vectors; no proposed native labels used by gate. Author saw outcomes, no prospective/heldout/joint admission claim.'),indent=2)+'\n')
print([(x['width'],x['index'],x['decision']['model_admitted']) for x in rows])
