"""Explicit candidate-set matching controls; no all-pin reachability inference."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from pin_assignment import assign
out=Path('experiments/frisc_pin_assignment_2026-10-05');rowfile=Path('experiments/frisc_packed_pin_witness_2026-10-05/rows.json');epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json')
if out.exists():raise ValueError('fresh output required')
e=json.loads(epath.read_text());inputs={str(rowfile):sha(rowfile),str(epath):sha(epath),e['inputs']['graph']['path']:e['inputs']['graph']['sha256']};assert all(sha(p)==h for p,h in inputs.items());start=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);catalog=PinChoiceCatalog(g);rows=json.loads(rowfile.read_text());candidate_sets={'selected_witness_only':{},'all_class_members_relaxation':{},'nominal_packed_mapping_only':{}}
for r in rows:
 cid=r['connection_id'];w=r['path_pin_witness'];sink=w['sink_class'];selected=w['selected_ipin_ptc'];nominal=r['packed_sink']['physical_pin_ptc'];pool=catalog.sinks[sink].physical_pins;assert selected in pool and nominal in pool
 candidate_sets['selected_witness_only'][cid]=[(sink,selected)];candidate_sets['all_class_members_relaxation'][cid]=[(sink,p) for p in pool];candidate_sets['nominal_packed_mapping_only'][cid]=[(sink,nominal)]
out.mkdir();reports=[]
for name,candidates in candidate_sets.items():
 t=time.monotonic();result=assign(candidates);wall=time.monotonic()-t
 if result['status']=='matched':
  assert len(result['assignment'])==len(rows) and len({tuple(v) for v in result['assignment'].values()})==len(rows);assert all(tuple(v) in candidates[c] for c,v in result['assignment'].items())
 else:
  w=result['hall_witness'];neighbors={p for cid in w['request_ids'] for p in candidates[cid]};assert neighbors=={tuple(p) for p in w['physical_pins']} and len(neighbors)<len(w['request_ids'])
 (out/f'{name}.json').write_text(json.dumps(result)+'\n');reports.append({'name':name,'status':result['status'],'matched_requests':len(result['assignment']),'hall_witness':result['hall_witness'],'wall_s':wall});print(json.dumps(reports[-1]),flush=True)
assert all(sha(p)==h for p,h in inputs.items());(out/'source').mkdir()
for name in ('frisc_pin_assignment_trial.py','pin_assignment.py','pin_choice_catalog.py','pin_pools.py'):(out/'source'/name).write_text(Path('tools',name).read_text())
receipt={'reports':reports,'requests':len(rows),'input_sha256':inputs,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'full_wall_s':time.monotonic()-start,'limitations':['each packed sink request requires distinct pin; differs from unique-net occupancy statistic','all-class and nominal-only sets not proven reachable from every source','no route repair performed; output assignment is not a routed solution','no prospective QoR or native timing conclusion']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
