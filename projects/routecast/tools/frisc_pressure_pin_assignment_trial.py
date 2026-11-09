import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from costed_pin_assignment import assign_costed
out=Path('experiments/frisc_pressure_pin_assignment_2026-10-05')
if out.exists():raise ValueError('fresh output required')
root=Path('experiments/frisc_reachable_pin_trial_2026-10-05');files=[root/'paths.json',root/'assignment.json',Path('experiments/frisc_pin_equivalence_audit_2026-10-05/receipt.json'),Path('work/frisc_graph_capture_2026-10-05/rr_graph.xml')];inputs={str(p):sha(p) for p in files}
background=Path('experiments/frisc_timing_backgrounds_v2_2026-10-05/baseline_prediction.json');inputs[str(background)]=sha(background)
start=time.monotonic();g=read_rr_graph(files[-1]);paths=json.loads(files[0].read_text());previous=json.loads(files[1].read_text());equivalence=json.loads(files[2].read_text());assert set(paths)=={str(r['cid']) for r in equivalence['checks']}
from net_pressure_sketch import net_union
bg=json.loads(background.read_text());users,demand=net_union(g,bg);nets={r['connection_id']:r['net_id'] for r in bg['connections']};costs={}
for cid,result in paths.items():
 options={}
 for ptc,path in result['paths'].items():
  value=0
  for eid in path:
   node=g.nodes[g.edges[eid].sink]
   if node.type in {'CHANX','CHANY'}:
    loc=dict(node.location);value+=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
    d=demand.get(node.id,0)-int(node.id in users[nets[int(cid)]])
    value+=(256*max(0,d-node.capacity+1)+node.capacity-1)//node.capacity
  options[10709,int(ptc)]=value
 costs[int(cid)]=options
old_cost=sum(costs[int(cid)][tuple(pin)] for cid,pin in previous['assignment'].items());t=time.monotonic();result=assign_costed(costs);solver_s=time.monotonic()-t;assert result['status']=='matched' and result['total_cost']<=old_cost
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'assignment.json').write_text(json.dumps(result)+'\n');(out/'costs.json').write_text(json.dumps({r:{str(p[1]):c for p,c in v.items()} for r,v in costs.items()})+'\n');(out/'source').mkdir()
for name in ('frisc_pressure_pin_assignment_trial.py','costed_pin_assignment.py','pin_assignment.py'):(out/'source'/name).write_text(Path('tools',name).read_text())
receipt={'requests':len(costs),'old_additive_channel_span':old_cost,'optimal_supplied_additive_channel_span':result['total_cost'],'changed_assignments':sum(pin!=previous['assignment'][str(cid)] for cid,pin in result['assignment'].items()),'solver_s':solver_s,'full_wall_s':time.monotonic()-start,'input_sha256':inputs,'source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')},'artifact_sha256':{n:sha(out/n) for n in ('assignment.json','costs.json')},'limitations':['costs on previously generated BFS paths only, not shortest weighted RR paths','connection-additive channel span differs from unique-net union span','frozen alpha256 own-net excluded channel penalty; not negotiated congestion or native QoR proof']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
