import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from reachable_pin_candidates import ReachablePins
from pin_assignment import assign
out=Path('experiments/frisc_reachable_pin_trial_2026-10-05')
if out.exists():raise ValueError('fresh output required')
rowfile=Path('experiments/frisc_packed_pin_witness_2026-10-05/rows.json')
epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json')
e=json.loads(epath.read_text());graphfile=e['inputs']['graph']['path']
inputs={str(rowfile):sha(rowfile),str(epath):sha(epath),graphfile:e['inputs']['graph']['sha256']}
assert all(sha(p)==h for p,h in inputs.items())
start=time.monotonic();g=read_rr_graph(graphfile);search=ReachablePins(g)
rows=[r for r in json.loads(rowfile.read_text()) if r['path_pin_witness']['sink_class']==10709]
results={};candidates={};query_start=time.monotonic()
for r in rows:
 cid=r['connection_id'];w=r['path_pin_witness'];t=time.monotonic()
 result=search.query(w['source_class'],w['sink_class'],r['packed_source']['physical_pin_ptc'])
 for ptc,path in result['paths'].items():
  v=search.catalog.witness(w['source_class'],w['sink_class'],path)
  assert v['selected_ipin_ptc']==ptc and v['selected_opin_ptc']==r['packed_source']['physical_pin_ptc']
 results[cid]=result;candidates[cid]=[(w['sink_class'],p) for p in result['paths']]
 print(json.dumps({'cid':cid,'reachable_physical_pins':len(result['paths']),'wall_s':time.monotonic()-t}),flush=True)
query_wall=time.monotonic()-query_start
assignment=assign(candidates)
if assignment['status']=='matched':
 assert len(assignment['assignment'])==len(rows) and len({tuple(v) for v in assignment['assignment'].values()})==len(rows)
 for cid,pin in assignment['assignment'].items():assert pin[1] in results[cid]['paths']
else:
 hall=assignment['hall_witness'];neighbors={p for cid in hall['request_ids'] for p in candidates[cid]}
 assert neighbors=={tuple(p) for p in hall['physical_pins']} and len(neighbors)<len(hall['request_ids'])
assert all(sha(p)==h for p,h in inputs.items())
out.mkdir();(out/'paths.json').write_text(json.dumps(results)+'\n');(out/'assignment.json').write_text(json.dumps(assignment)+'\n');(out/'source').mkdir()
for name in ('frisc_reachable_pin_trial.py','reachable_pin_candidates.py','pin_assignment.py','pin_choice_catalog.py','pin_pools.py','rr_graph.py'):
 (out/'source'/name).write_text(Path('tools',name).read_text())
receipt={'requests':len(rows),'sink_class':10709,'status':assignment['status'],'query_wall_s':query_wall,'full_wall_s':time.monotonic()-start,'candidate_counts':{cid:len(r['paths']) for cid,r in results.items()},'input_sha256':inputs,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'artifact_sha256':{name:sha(out/name) for name in ('paths.json','assignment.json')},'limitations':['single conflict class, not full design','fixed nominal source physical pin; graph sink class members only, packed pin interchangeability not proven','paths ignore channel congestion and joint-net tree constraints','no native QoR or timing improvement claim']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
