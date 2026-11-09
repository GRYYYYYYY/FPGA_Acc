"""Inventory unused valid same-run detours, without claiming their route outcome."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_preserved_budget_online_loop_2026-10-06';out=ROOT/'experiments/mux_preserved_budget_branch_analysis_2026-10-06';out.mkdir(exist_ok=True);rows=[];bindings={}
for file in sorted(base.glob('w*_m*/result.json')):
 d=json.loads(file.read_text());bindings[str(file)]=sha(file)
 for j,t in enumerate(d['result']['trace'][:-1]):
  if 'options' not in t:continue
  current=d['attempts'][j]['allocation_index'];selected=d['attempts'][j+1]['allocation_index'];next_current=d['attempts'][j+1]['allocation_index'];specs=[s for s in d['allocations'] if current<s['index'] and s['restrictions'] in [o['restrictions'] for o in t['options']]]
  # Restrictions strictly accumulate; identical proposals cannot belong to a later level.
  assert len(specs)==len(t['options']);valid=[s for s in specs if s['valid']];best=min(valid,key=lambda s:(F(s['floor_cpd_ns']),F(s['total_floor_increase_ns']),s['index']));assert best['index']==selected
  rows.append(dict(case=file.parent.name,attempt=j,selected=selected,valid_options=len(valid),unused_valid_options=[s['index'] for s in valid if s['index']!=selected],primary_all_tie=len({s['floor_cpd_ns'] for s in valid})==1,next_completed=d['result']['trace'][j+1]['candidate']['completed_connections'],current_completed=t['candidate']['completed_connections']))
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='Available completed-file snapshot: unused accepted allocation options, not routed alternative outcomes or regret/optimality proof. Only original same-run option records examined, no cold/future route oracle.'),indent=2)+'\n');print('decisions',len(rows),'unused valid',sum(len(r['unused_valid_options']) for r in rows),'nonimproving chosen coverage',sum(r['next_completed']<=r['current_completed'] for r in rows))
