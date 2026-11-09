"""Replay frozen cohort states; evaluate new feasibility, not new commits."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_budget_pin_candidates import PreparedBudgetPins
from buffered_delay_cost import BufferedDelayCost
from net_pressure_sketch import net_union
from free_pin_delay_prefilter import feasible_targets

out=Path('experiments/alu4_free_pin_prefilter_replay_v3_2026-10-05')
if out.exists():raise ValueError('fresh output required')
out.mkdir(); start=time.monotonic()
root=Path('experiments/alu4_free_pin_cohort_2026-10-05')
inputs=[root/'receipt.json',root/'query_candidates.json',Path('experiments/alu4_free_pin_budget_trial_2026-10-05/prediction.json'),Path('work/alu4_validation_capture_2026-10-05/rr_graph.xml')]
hashes={str(p):sha(p) for p in inputs}
(out/'protocol.json').write_text(json.dumps({'inputs':hashes,'source_sha256':sha(__file__),'prefilter_sha256':sha('tools/free_pin_delay_prefilter.py'),'scope':'All 1012 original states; archived commits replayed, no fresh optimization or native validation'},indent=2)+'\n')
g=read_rr_graph(inputs[-1]);engine=PreparedBudgetPins(g);model=BufferedDelayCost(g)
original={r['connection_id']:r for r in json.loads(inputs[2].read_text())['connections']};rows=dict(original)
receipt=json.loads(inputs[0].read_text());attempts=json.loads(inputs[1].read_text());incoming=defaultdict(list)
for eid,edge in enumerate(g.edges):incoming[edge.sink].append(eid)
records=[];net=None
for report,attempt in zip(receipt['reports'],attempts):
 cid=report['cid'];assert cid==attempt['cid'];old=rows[cid]
 if old['net_id']!=net:
  net=old['net_id'];users=defaultdict(set)
  for row in rows.values():users[row['net_id']].update({row['source']}|{g.edges[e].sink for e in row['physical_edge_ids']})
  demand=Counter(node for nodes in users.values() for node in nodes)
  blocked={n for n,node in g.nodes.items() if node.type in {'CHANX','CHANY'} and demand.get(n,0)-int(n in users[net])>=node.capacity}
  context=engine.prepare([0]*len(g.edges),model.weights,blocked)
 edges={e for r in rows.values() if r['net_id']==net and r['connection_id']!=cid for e in r['physical_edge_ids']}
 parents={g.edges[e].sink:e for e in edges};assert len(parents)==len(edges)
 forbidden={e for node,parent in parents.items() for e in incoming[node] if e!=parent}
 witness=engine.catalog.witness(old['source'],old['sink'],old['physical_edge_ids'])
 targets=[q['selected_ipin_ptc'] for q in attempt['targets']]
 budget=sum(model.weights[e] for e in original[cid]['physical_edge_ids'])
 t=time.monotonic();result=feasible_targets(engine,context,old['source'],old['sink'],witness['selected_opin_ptc'],targets,budget,forbidden);wall=time.monotonic()-t
 expected=sorted(q['selected_ipin_ptc'] for q in attempt['targets'] if q['status']=='FOUND')
 assert not any(q['status']=='LABEL_LIMIT' for q in attempt['targets'])
 assert result['feasible_targets']==expected,(cid,result['feasible_targets'],expected)
 records.append({'cid':cid,'target_count':len(targets),'wall_s':wall,**result})
 if report['committed']:
  best=min((q for q in attempt['targets'] if q['status']=='FOUND'),key=lambda q:(q['cost'],q['delay'],q['selected_ipin_ptc']))
  rows[cid]={**old,'physical_edge_ids':best['path'],'method':'incremental_budget_free_pin_branch'}
 (out/'progress.json').write_text(json.dumps({'completed':len(records),'latest':records[-1],'prefilter_wall_s':sum(r['wall_s'] for r in records)})+'\n')
 if len(records)%50==0:print(json.dumps({'completed':len(records),'wall_s':time.monotonic()-start}),flush=True)
final=json.loads((root/'prediction.json').read_text());assert rows=={r['connection_id']:r for r in final['connections']}
assert all(sha(p)==h for p,h in hashes.items())
(out/'results.json').write_text(json.dumps(records)+'\n')
(out/'receipt.json').write_text(json.dumps({'requests':len(records),'all_target_status_sets_equal':True,'replayed_final_records_exact':True,'prefilter_wall_s':sum(r['wall_s'] for r in records),'examined_edges':sum(r['examined_edges'] for r in records),'full_wall_s':time.monotonic()-start,'scope':'Feasibility-only replay; downstream cost searches omitted, not end-to-end speedup'},indent=2)+'\n')
print((out/'receipt.json').read_text(),flush=True)
