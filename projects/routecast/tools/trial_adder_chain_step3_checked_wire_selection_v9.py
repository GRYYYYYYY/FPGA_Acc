"""Greedy legal path substitutions minimizing whole-selection distinctNET channel geometry."""
import json,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_chain_step3_checked_wire_selection_v9_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_chain_step3_checked_native_quality_v9_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';_,_,nodes,f,rc,_=load_endpoints(ep);q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};bankp=E/'adder_chain_step3_checked_v9_2026-10-09/result.json';bank={int(c):o for c,o in json.loads(bankp.read_text())['bank'].items()};sp=E/'adder_chain_step3_checked_verification_v9_2026-10-09/selection.json';selection={int(c):i for c,i in json.loads(sp.read_text())['selection'].items()};length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1

def evaluate(selection):
 owners=defaultdict(set);parents=defaultdict(dict)
 for cid,index in selection.items():
  net=q[cid]['net_id'];path=bank[cid][index]['path']
  for n,s in path:owners[n].add(net)
  for (u,_),(n,s) in zip(path,path[1:]):
   if n in parents[net] and parents[net][n]!=(u,s):return None
   parents[net][n]=(u,s)
 if any(len(nets)>f['capacities'][n] for n,nets in owners.items()):return None
 return sum(length.get(n,0)*len(nets) for n,nets in owners.items())
start=time.perf_counter();cost=evaluate(selection);assert cost is not None;initial=cost;events=[]
for iteration in range(10):
 changed=False
 for cid in sorted(selection):
  old=selection[cid];best=old;bestcost=cost
  for index in range(len(bank[cid])):
   if index==old:continue
   selection[cid]=index;value=evaluate(selection)
   if value is not None and value<bestcost:best=index;bestcost=value
  selection[cid]=best
  if best!=old:events.append(dict(iteration=iteration,connection_id=cid,old_index=old,new_index=best,old_cost=cost,new_cost=bestcost));cost=bestcost;changed=True
 if not changed:break
p=D/'selection.json';p.write_text(json.dumps(dict(selection=selection,paths={c:bank[c][i]['path'] for c,i in selection.items()},events=events),indent=2)+'\n')
for p in (p,ep,bankp,sp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,initial_geometry=initial,final_geometry=cost,accepted_substitutions=len(events),seconds=time.perf_counter()-start,scope='Greedy existing-bank path substitution with full capacity/parent checks. Geometry proxy requires independent selected-path and native wirelength audit; no optimum or performance gain claim.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
